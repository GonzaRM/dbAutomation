from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + '/app/roles.db' 
app.config["JWT_SECRET_KEY"] = "meli2024*"
db = SQLAlchemy(app)
jwt = JWTManager(app)

# Endpoint para login (genera un token JWT)
@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username', None)
    password = request.json.get('password', None)

    # 1. Validación de entrada:
    if not username or not password:
        return jsonify({"msg": "Missing username or password"}), 400  # Bad Request

    user = User.query.filter_by(username=username).first()

    # 4. Generación del token JWT:
    access_token = create_access_token(identity=username)
    return jsonify(access_token=access_token)

# Modelos de datos
class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(255))
    type = db.Column(db.String(50))
    scope = db.Column(db.String(255))
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'type': self.type,
            'scope': self.scope
    }

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)

class UserRole(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=False)
    
# Endpoints
@app.route('/roles', methods=['POST'])
@jwt_required()
def create_role():
    try:
        role_data = request.get_json(force=True)

        # Valido los datos
        if not role_data.get('name'):
            return jsonify({'error': 'Falta el campo requerido: nombre'}), 400

        # Verifico tipo de dato
        if not isinstance(role_data.get('name'), str) or \
           not isinstance(role_data.get('description'), (str, type(None))) or \
           not isinstance(role_data.get('type'), (str, type(None))) or \
           not isinstance(role_data.get('scope'), (str, type(None))):
            return jsonify({'error': 'Tipos de datos inválidos'}), 400

        # Verifico si ya existe
        existing_role = Role.query.filter_by(name=role_data['name']).first()
        if existing_role:
            return jsonify({'error': 'Ya existe un rol con ese nombre'}), 400

        # Puedo agregar otras validaciones de negocio..

        new_role = Role(
            name=role_data['name'],
            description=role_data.get('description'),
            type=role_data.get('type'),
            scope=role_data.get('scope')
        )
        db.session.add(new_role)
        db.session.commit()
        return jsonify({'mensaje': 'Rol creado exitosamente', 'role_id': new_role.id}), 201

    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Ya existe un rol con ese nombre'}), 400

    except Exception as e:
        db.session.rollback()
        # logging
        return jsonify({'error': 'Ocurrió un error al crear el rol'}), 500

@app.route('/roles/<int:role_id>', methods=['PUT'])
@jwt_required()
def update_role(role_id):
    try:
        role = Role.query.get_or_404(role_id)
        data = request.get_json()

        # Valido los datos
        if not isinstance(data.get('name'), (str, type(None))) or \
           not isinstance(data.get('description'), (str, type(None))) or \
           not isinstance(data.get('type'), (str, type(None))) or \
           not isinstance(data.get('scope'), (str, type(None))):
            return jsonify({'error': 'Tipos de datos inválidos'}), 400

        # Verifico si el nuevo nombre existe
        if 'name' in data:
            existing_role = Role.query.filter(Role.id != role_id, Role.name == data['name']).first()
            if existing_role:
                return jsonify({'error': 'Ya existe un rol con ese nombre'}), 400

        # Actualizo los campos del rol
        role.name = data.get('name', role.name)
        role.description = data.get('description', role.description)
        role.type = data.get('type', role.type)
        role.scope = data.get('scope', role.scope)

        db.session.commit()
        return jsonify({'mensaje': 'Rol actualizado exitosamente'})

    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Ya existe un rol con ese nombre'}), 400

    except Exception as e:
        db.session.rollback()
        # logging
        return jsonify({'error': 'Ocurrió un error al actualizar el rol'}), 500

@app.route('/roles', methods=['GET'])
@jwt_required()
def get_all_roles():
    try:
        roles = Role.query.all()
        return jsonify([role.to_dict() for role in roles])

    except Exception as e:
        # logging
        return jsonify({'error': 'Ocurrió un error al obtener los roles'}), 500

@app.route('/user_roles/<int:user_id>/<int:role_id>', methods=['POST'])
@jwt_required()
def assign_role_to_user(user_id, role_id):
    try:
        data = request.get_json()

        # Valido los datos
        if not data.get('user_id') or not data.get('role_id'):
            return jsonify({'error': 'Faltan campos requeridos: user_id y/o role_id'}), 400

        if not isinstance(data.get('user_id'), int) or not isinstance(data.get('role_id'), int):
            return jsonify({'error': 'Tipos de datos inválidos para user_id y/o role_id'}), 400

        # Verifico si el usuario y el rol existen
        user = User.query.get(data['user_id'])
        role = Role.query.get(data['role_id'])

        if not user or not role:
            return jsonify({'error': 'Usuario o rol no encontrado'}), 404

        # Verifico si ya se encuentra asociado
        existing_association = UserRole.query.filter_by(user_id=data['user_id'], role_id=data['role_id']).first()
        if existing_association:
            return jsonify({'error': 'El usuario ya tiene asignado ese rol'}), 400

        new_user_role = UserRole(user_id=data['user_id'], role_id=data['role_id'])
        db.session.add(new_user_role)
        db.session.commit()
        return jsonify({'mensaje': 'Rol asignado al usuario exitosamente'}), 201

    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Error de integridad en la base de datos. Es posible que la asociación ya exista o que los IDs de usuario o rol sean inválidos.'}), 400

    except Exception as e:
        db.session.rollback()
        # logging
        return jsonify({'error': 'Ocurrió un error al asignar el rol al usuario'}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Va a crear las tablas si no existen
    app.run(debug=True, host='0.0.0.0') 
