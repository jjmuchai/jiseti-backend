from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class NormalUser(db.Model):
    __tablename__ = 'normal_users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(512), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    email_verified = db.Column(db.Boolean, default=False)
    phone_number = db.Column(db.String(20), nullable=True) 

    # Relationships
    records = db.relationship('Record', backref='normal_user', lazy=True, cascade="all, delete-orphan")
    votes = db.relationship('Vote', backref='user', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active,
            'email_verified': self.email_verified
        }

    def __repr__(self):
        return f"<NormalUser {self.name}>"

class Administrator(db.Model):
    __tablename__ = 'administrators'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    admin_number = db.Column(db.String(50), unique=True, nullable=False)
    role = db.Column(db.String(20), default='admin')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'admin_number': self.admin_number,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

    def __repr__(self):
        return f"<Administrator {self.name}, AdminNumber={self.admin_number}>"

class Record(db.Model):
    __tablename__ = 'records'

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(20), nullable=False)  
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default="draft")  
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    location_name = db.Column(db.String(255), nullable=True) 
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolution_notes = db.Column(db.Text, nullable=True)  
    is_anonymous = db.Column(db.Boolean, default=False)  
    vote_count = db.Column(db.Integer, default=0)  
    urgency_level = db.Column(db.String(20), default='medium')  
    
    # Foreign Keys
    normal_user_id = db.Column(db.Integer, db.ForeignKey('normal_users.id'), nullable=True) 
    assigned_admin_id = db.Column(db.Integer, db.ForeignKey('administrators.id'), nullable=True)

    # Relationships
    media = db.relationship("Media", backref="record", cascade="all, delete-orphan")
    votes = db.relationship("Vote", backref="record", cascade="all, delete-orphan")
    status_history = db.relationship("StatusHistory", backref="record", cascade="all, delete-orphan")

    def to_dict(self):
        """Convert record to dictionary for API responses"""
    
        media = self.media[0] if self.media else None
        
        return {
            "id": self.id,
            "type": self.type,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "location_name": self.location_name,
            "urgency_level": self.urgency_level,
            "vote_count": self.vote_count,
            "is_anonymous": self.is_anonymous,
            "resolution_notes": self.resolution_notes,
            "normal_user_id": self.normal_user_id,
            "assigned_admin_id": self.assigned_admin_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            
            
            "image_url": media.image_url if media and media.image_url else None,
            "video_url": media.video_url if media and media.video_url else None,
            
            
            "media": [m.to_dict() for m in self.media],
            
            # Creator info (only for non-anonymous)
            "creator_name": self.normal_user.name if self.normal_user and not self.is_anonymous else "Anonymous",
        }

    def to_public_dict(self):
        """Public view without sensitive information"""
        data = self.to_dict()
        
        if self.is_anonymous or True:  
            data.pop('normal_user_id', None)
            data['creator_name'] = "Anonymous"
        return data

class Media(db.Model):
    __tablename__ = 'media'

    id = db.Column(db.Integer, primary_key=True)
    record_id = db.Column(db.Integer, db.ForeignKey("records.id"), nullable=False)
    media_type = db.Column(db.String(10), nullable=False) 
    media_url = db.Column(db.Text, nullable=False)
    filename = db.Column(db.String(255), nullable=True)
    file_size = db.Column(db.Integer, nullable=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    

    image_url = db.Column(db.String, nullable=True)
    video_url = db.Column(db.String, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "record_id": self.record_id,
            "media_type": self.media_type,
            "media_url": self.media_url,
            "filename": self.filename,
            "file_size": self.file_size,
            "uploaded_at": self.uploaded_at.isoformat(),
            "image_url": self.image_url,
            "video_url": self.video_url
        }

class Vote(db.Model):
    __tablename__ = 'votes'

    id = db.Column(db.Integer, primary_key=True)
    record_id = db.Column(db.Integer, db.ForeignKey('records.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('normal_users.id'), nullable=False)
    vote_type = db.Column(db.String(10), default='support')  
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    
    __table_args__ = (db.UniqueConstraint('record_id', 'user_id', name='unique_user_vote'),)

    def to_dict(self):
        return {
            "id": self.id,
            "record_id": self.record_id,
            "user_id": self.user_id,
            "vote_type": self.vote_type,
            "created_at": self.created_at.isoformat()
        }

class StatusHistory(db.Model):
    __tablename__ = 'status_history'

    id = db.Column(db.Integer, primary_key=True)
    record_id = db.Column(db.Integer, db.ForeignKey('records.id'), nullable=False)
    old_status = db.Column(db.String(50), nullable=True)
    new_status = db.Column(db.String(50), nullable=False)
    changed_by = db.Column(db.Integer, db.ForeignKey('administrators.id'), nullable=True)
    change_reason = db.Column(db.Text, nullable=True)
    changed_at = db.Column(db.DateTime, default=datetime.utcnow)


    admin = db.relationship('Administrator', backref='status_changes')

    def to_dict(self):
        return {
            "id": self.id,
            "record_id": self.record_id,
            "old_status": self.old_status,
            "new_status": self.new_status,
            "changed_by": self.changed_by,
            "admin_name": self.admin.name if self.admin else "System",
            "change_reason": self.change_reason,
            "changed_at": self.changed_at.isoformat()
        }

class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    record_id = db.Column(db.Integer, db.ForeignKey('records.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('normal_users.id'), nullable=True)
    notification_type = db.Column(db.String(20), nullable=False)  
    message = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    delivery_status = db.Column(db.String(20), default='pending') 
    external_id = db.Column(db.String(100), nullable=True) 

    def to_dict(self):
        return {
            "id": self.id,
            "record_id": self.record_id,
            "user_id": self.user_id,
            "notification_type": self.notification_type,
            "message": self.message,
            "sent_at": self.sent_at.isoformat(),
            "delivery_status": self.delivery_status,
            "external_id": self.external_id
        }
