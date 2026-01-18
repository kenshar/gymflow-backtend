import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
from dotenv import load_dotenv  


load_dotenv()

app = Flask(__name__)
CORS(app)



app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)



class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    membership_type = db.Column(db.String(20), default='Standard')  # Standard, Premium, VIP
    join_date = db.Column(db.Date, default=datetime.utcnow)
    membership_end_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), default='Active')  # Active, Expired, Canceled

    def to_dict(self):
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email,
            'phone': self.phone,
            'membership_type': self.membership_type,
            'join_date': self.join_date.strftime('%Y-%m-%d') if self.join_date else None,
            'membership_end_date': self.membership_end_date.strftime('%Y-%m-%d') if self.membership_end_date else None,
            'status': self.status
        }




@app.route('/members', methods=['POST'])
def add_member():
    data = request.get_json()
    
    
    if not data or not data.get('email'):
        return jsonify({'error': 'Email is required'}), 400

    try:
        
        end_date = None
        if 'membership_end_date' in data and data['membership_end_date']:
            end_date = datetime.strptime(data['membership_end_date'], '%Y-%m-%d').date()

        new_member = Member(
            first_name=data['first_name'],
            last_name=data['last_name'],
            email=data['email'],
            phone=data.get('phone', ''),
            membership_type=data.get('membership_type', 'Standard'),
            membership_end_date=end_date,
            status=data.get('status', 'Active')
        )

        db.session.add(new_member)
        db.session.commit()
        return jsonify({'message': 'Member added successfully', 'member': new_member.to_dict()}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/members', methods=['GET'])
def get_members():
    members = Member.query.all()
    return jsonify([m.to_dict() for m in members]), 200


@app.route('/members/<int:id>', methods=['GET'])
def get_member(id):
    member = Member.query.get_or_404(id)
    return jsonify(member.to_dict()), 200


@app.route('/members/<int:id>', methods=['PUT'])
def update_member(id):
    member = Member.query.get_or_404(id)
    data = request.get_json()

    member.first_name = data.get('first_name', member.first_name)
    member.last_name = data.get('last_name', member.last_name)
    member.phone = data.get('phone', member.phone)
    member.membership_type = data.get('membership_type', member.membership_type)
    member.status = data.get('status', member.status)

    if 'membership_end_date' in data and data['membership_end_date']:
         member.membership_end_date = datetime.strptime(data['membership_end_date'], '%Y-%m-%d').date()

    db.session.commit()
    return jsonify({'message': 'Member updated successfully', 'member': member.to_dict()}), 200


@app.route('/members/<int:id>', methods=['DELETE'])
def delete_member(id):
    member = Member.query.get_or_404(id)
    db.session.delete(member)
    db.session.commit()
    return jsonify({'message': 'Member deleted successfully'}), 200


with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
