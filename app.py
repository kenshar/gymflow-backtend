from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app)


app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://gymflow:password123@localhost/gymflow_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class Member(db.Model):
    __tablename__ = 'members'
    
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    status = db.Column(db.String(20), default='active') 
    membership_end_date = db.Column(db.Date, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'firstName': self.first_name,
            'lastName': self.last_name,
            'email': self.email,
            'status': self.status,
            'membershipEndDate': str(self.membership_end_date)
        }



@app.route('/api/members', methods=['POST'])
def create_member():
    data = request.json
    try:
        new_member = Member(
            first_name=data['firstName'],
            last_name=data['lastName'],
            email=data['email'],
            phone=data.get('phone', ''),
            membership_end_date=datetime.strptime(data['membershipEndDate'], '%Y-%m-%d').date()
        )
        db.session.add(new_member)
        db.session.commit()
        return jsonify(new_member.to_dict()), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/members', methods=['GET'])
def get_members():
    members = Member.query.all()
    return jsonify([m.to_dict() for m in members])


@app.route('/api/members/<int:id>', methods=['DELETE'])
def delete_member(id):
    try:
        member = Member.query.get(id)
        if member:
            db.session.delete(member)
            db.session.commit()
            return jsonify({'message': 'Member deleted'}), 200
        return jsonify({'error': 'Member not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
