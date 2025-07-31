from flask import Blueprint, request, jsonify, make_response
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
from models import db, NormalUser, Record, Administrator, Media, Vote, StatusHistory, Notification
from utils.emailer import send_status_email, send_welcome_email, send_record_created_email, send_sms_notification
from utils.validators import validate_email, validate_media_url, validate_coordinates
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from uuid import uuid4
import logging
import re
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

routes = Blueprint('routes', __name__)

# ------------------ Helper Functions -------------

def get_pagination_params(request):
    """Extract and validate pagination parameters from request"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        
        if page < 1:
            page = 1
        if per_page < 1 or per_page > 100:
            per_page = 10
            
        return page, per_page
    except (ValueError, TypeError):
        return 1, 10

def create_status_history(record_id, old_status, new_status, admin_id=None, reason=None):
    """Create status history record"""
    try:
        history = StatusHistory(
            record_id=record_id,
            old_status=old_status,
            new_status=new_status,
            changed_by=admin_id,
            change_reason=reason
        )
        db.session.add(history)
        return True
    except Exception as e:
        logger.error(f"Failed to create status history: {str(e)}")
        return False

def update_vote_count(record_id):
    """Update vote count for a record"""
    try:
        vote_count = Vote.query.filter_by(record_id=record_id).count()
        record = Record.query.get(record_id)
        if record:
            record.vote_count = vote_count
        return vote_count
    except Exception as e:
        logger.error(f"Failed to update vote count: {str(e)}")
        return 0

# ------------------ Authentication Endpoints ------------------

@routes.route('/auth/signup', methods=['POST'])
def signup():
    """User registration endpoint"""
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['name', 'email', 'password']
    if not all(data.get(field) for field in required_fields):
        return make_response({'error': 'Name, email, and password are required'}, 400)

    # Validate email format (Gmail only as per requirements)
    if not validate_email(data['email']):
        return make_response({'error': 'Email must be a valid Gmail address (@gmail.com)'}, 400)

    # Check if user already exists
    if NormalUser.query.filter_by(email=data['email']).first():
        return make_response({'error': 'User with this email already exists'}, 409)

    # Validate password strength
    password = data['password']
    if len(password) < 6:
        return make_response({'error': 'Password must be at least 6 characters long'}, 400)

    try:
        new_user = NormalUser(
            name=data['name'],
            email=data['email'],
            password=generate_password_hash(password),
            phone_number=data.get('phone_number')  # Optional for SMS
        )

        db.session.add(new_user)
        db.session.commit()

        # Send welcome email
        send_welcome_email(new_user.email, new_user.name)

        # Generate JWT token
        token = create_access_token(identity={'id': new_user.id, 'role': 'user'})
        
        return make_response({
            'message': 'User created successfully',
            'access_token': token,
            'user': new_user.to_dict()
        }, 201)

    except Exception as e:
        db.session.rollback()
        logger.error(f"User signup failed: {str(e)}")
        return make_response({'error': 'User signup failed'}, 500)

@routes.route('/auth/login', methods=['POST'])
def login():
    """User login endpoint"""
    data = request.get_json()
    if not data or not data.get('email') or not data.get('password'):
        return make_response({'error': 'Email and password are required'}, 400)

    try:
        user = NormalUser.query.filter_by(email=data['email']).first()
        if user and check_password_hash(user.password, data['password']):
            if not user.is_active:
                return make_response({'error': 'Account is deactivated'}, 403)
                
            token = create_access_token(identity={'id': user.id, 'role': 'user'})
            return make_response({
                'message': 'Login successful',
                'access_token': token,
                'user': user.to_dict()
            }, 200)

        return make_response({'error': 'Invalid credentials'}, 401)
    except Exception as e:
        logger.error(f"Login failed: {str(e)}")
        return make_response({'error': 'Login failed'}, 500)

@routes.route('/admin/signup', methods=['POST'])
def admin_signup():
    """Admin registration endpoint"""
    data = request.get_json()

    required_fields = ['name', 'email', 'password']
    if not all(data.get(field) for field in required_fields):
        return make_response({'error': 'Name, email, and password are required'}, 400)

    if Administrator.query.filter_by(email=data['email']).first():
        return make_response({'error': 'Admin with this email already exists'}, 409)

    admin_number = f"ADM-{uuid4().hex[:8].upper()}"

    try:
        new_admin = Administrator(
            name=data['name'],
            email=data['email'],
            password=generate_password_hash(data['password']),
            admin_number=admin_number
        )

        db.session.add(new_admin)
        db.session.commit()

        token = create_access_token(identity={'id': new_admin.id, 'role': 'admin'})
        return make_response({
            'message': 'Admin account created successfully',
            'access_token': token,
            'admin': new_admin.to_dict()
        }, 201)

    except Exception as e:
        db.session.rollback()
        logger.error(f"Admin signup failed: {str(e)}")
        return make_response({'error': 'Admin signup failed'}, 500)

@routes.route('/admin/login', methods=['POST'])
def admin_login():
    """Admin login endpoint"""
    data = request.get_json()
    if not data or not data.get('email') or not data.get('password'):
        return make_response({'error': 'Email and password are required'}, 400)
    
    try:
        admin = Administrator.query.filter_by(email=data['email']).first()
        if admin and check_password_hash(admin.password, data['password']):
            # Update last login
            admin.last_login = datetime.utcnow()
            db.session.commit()
            
            token = create_access_token(identity={'id': admin.id, 'role': 'admin'})
            return make_response({
                'message': 'Admin login successful',
                'access_token': token,
                'admin': admin.to_dict()
            }, 200)
        return make_response({'error': 'Invalid admin credentials'}, 401)
    except Exception as e:
        logger.error(f"Admin login failed: {str(e)}")
        return make_response({'error': 'Admin login failed'}, 500)

# ------------------ Public Endpoints (No Authentication Required) ------------------

@routes.route('/public/records', methods=['GET'])
def get_public_records():
    """Get all records for public viewing (anonymous access) with enhanced search and filtering"""
    try:
        page, per_page = get_pagination_params(request)
        
        # Enhanced filters with search support
        status_filter = request.args.get('status')
        type_filter = request.args.get('type')
        urgency_filter = request.args.get('urgency')
        search_term = request.args.get('search', '').strip()
        
        # Build query - only show non-draft records publicly
        query = Record.query.filter(Record.status != 'draft')
        
        # Apply filters
        if status_filter and status_filter != 'all':
            query = query.filter(Record.status == status_filter)
        if type_filter and type_filter != 'all':
            query = query.filter(Record.type == type_filter)
        if urgency_filter and urgency_filter != 'all':
            query = query.filter(Record.urgency_level == urgency_filter)
        
        # Apply search functionality
        if search_term:
            # Search in title, description, and location
            search_filter = f"%{search_term}%"
            query = query.filter(
                db.or_(
                    Record.title.ilike(search_filter),
                    Record.description.ilike(search_filter),
                    Record.location_name.ilike(search_filter)
                )
            )
        
        # Order by vote count and creation date
        query = query.order_by(Record.vote_count.desc(), Record.created_at.desc())
        
        # Paginate
        paginated_records = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return make_response({
            'records': [r.to_public_dict() for r in paginated_records.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': paginated_records.total,
                'pages': paginated_records.pages,
                'has_next': paginated_records.has_next,
                'has_prev': paginated_records.has_prev
            },
            'search': {
                'term': search_term,
                'filters': {
                    'status': status_filter,
                    'type': type_filter,
                    'urgency': urgency_filter
                }
            }
        }, 200)
        
    except Exception as e:
        logger.error(f"Failed to fetch public records: {str(e)}")
        return make_response({'error': 'Failed to fetch records'}, 500)

@routes.route('/public/records/<int:record_id>', methods=['GET'])
def get_public_record_details(record_id):
    """Get specific record details for public viewing"""
    try:
        record = Record.query.get_or_404(record_id)
        
        # Only show non-draft records publicly
        if record.status == 'draft':
            return make_response({'error': 'Record not found'}, 404)
        
        return make_response({
            'record': record.to_public_dict(),
            'status_history': [h.to_dict() for h in record.status_history]
        }, 200)
        
    except Exception as e:
        logger.error(f"Failed to fetch public record: {str(e)}")
        return make_response({'error': 'Failed to fetch record'}, 500)

@routes.route('/public/report', methods=['POST'])
def anonymous_report():
    """Create anonymous report without authentication"""
    data = request.get_json()
    
    # Validate required fields
    if not data.get('title') or not data.get('description'):
        return make_response({'error': 'Title and description are required'}, 400)
    
    # Validate type
    valid_types = ['red-flag', 'intervention', 'incident', 'complaint', 'suggestion', 'emergency']
    if data.get('type') not in valid_types:
        return make_response({'error': f'Type must be one of: {", ".join(valid_types)}'}, 400)
    
    try:
        # Create anonymous record
        new_record = Record(
            title=data.get('title'),
            description=data.get('description'),
            type=data.get('type'),
            latitude=data.get('latitude'),
            longitude=data.get('longitude'),
            location_name=data.get('location_name'),
            urgency_level=data.get('urgency_level', 'medium'),
            status='under-investigation',  # Anonymous reports go straight to investigation
            is_anonymous=True,
            normal_user_id=None  # No user associated
        )

        db.session.add(new_record)
        db.session.flush()

        # Add media if provided
        if data.get('image_url') or data.get('video_url'):
            media = Media(
                record_id=new_record.id,
                image_url=data.get('image_url'),
                video_url=data.get('video_url'),
                media_type='image' if data.get('image_url') else 'video',
                media_url=data.get('image_url') or data.get('video_url')
            )
            db.session.add(media)

        db.session.commit()

        # Generate tracking token for anonymous user
        tracking_token = f"ANON-{new_record.id}-{uuid4().hex[:8].upper()}"

        return make_response({
            'message': 'Anonymous report submitted successfully',
            'tracking_token': tracking_token,
            'record_id': new_record.id,
            'record': new_record.to_public_dict()
        }, 201)

    except Exception as e:
        db.session.rollback()
        logger.error(f"Anonymous report creation failed: {str(e)}")
        return make_response({'error': 'Failed to create anonymous report'}, 500)

# ------------------ User Record Management ------------------

@routes.route('/records', methods=['POST'])
@jwt_required()
def create_record():
    """Create new record (authenticated users)"""
    identity = get_jwt_identity()
    if identity.get('role') != 'user':
        return make_response({'error': 'Only users can create records'}, 403)

    data = request.get_json()
    if not data.get('title'):
        return make_response({'error': 'Title is required'}, 400)

    # Validate type
    if data.get('type') not in ['red-flag', 'intervention', 'incident', 'complaint', 'suggestion', 'emergency']:
        data['type'] = 'red-flag'  # Default fallback

    # Validate coordinates if provided
    if data.get('latitude') is not None or data.get('longitude') is not None:
        if not validate_coordinates(data.get('latitude'), data.get('longitude')):
            return make_response({'error': 'Invalid coordinates provided'}, 400)

    # Validate media URLs if provided
    image_url = data.get('image_url')
    video_url = data.get('video_url')
    
    if image_url and not validate_media_url(image_url, 'image'):
        return make_response({'error': 'Invalid image URL format'}, 400)
    
    if video_url and not validate_media_url(video_url, 'video'):
        return make_response({'error': 'Invalid video URL format'}, 400)

    try:
        new_record = Record(
            title=data.get('title'),
            description=data.get('description', ''),
            type=data.get('type', 'red-flag'),
            latitude=data.get('latitude'),
            longitude=data.get('longitude'),
            location_name=data.get('location_name'),
            urgency_level=data.get('urgency_level', 'medium'),
            status='draft',
            normal_user_id=identity['id'],
            is_anonymous=False
        )

        db.session.add(new_record)
        db.session.flush()

        # Add media if provided
        if image_url or video_url:
            media = Media(
                record_id=new_record.id,
                image_url=image_url,
                video_url=video_url,
                media_type='image' if image_url else 'video',
                media_url=image_url or video_url
            )
            db.session.add(media)

        db.session.commit()

        # Send confirmation email
        user = NormalUser.query.get(identity['id'])
        send_record_created_email(user.email, user.name, new_record.title)

        return make_response({
            'message': 'Record created successfully',
            'record': new_record.to_dict()
        }, 201)

    except Exception as e:
        db.session.rollback()
        logger.error(f"Record creation failed: {str(e)}")
        return make_response({'error': 'Failed to create record'}, 500)

@routes.route('/my-records', methods=['GET'])
@jwt_required()
def get_my_records():
    """Get current user's records with search and filtering"""
    identity = get_jwt_identity()
    if identity.get('role') != 'user':
        return make_response({'error': 'Only users can view their records'}, 403)

    try:
        page, per_page = get_pagination_params(request)
        
        # Enhanced filtering with search
        status_filter = request.args.get('status')
        type_filter = request.args.get('type')
        search_term = request.args.get('search', '').strip()
        
        query = Record.query.filter_by(normal_user_id=identity['id'])
        
        # Apply filters
        if status_filter and status_filter != 'all':
            query = query.filter(Record.status == status_filter)
        if type_filter and type_filter != 'all':
            query = query.filter(Record.type == type_filter)
        
        # Apply search
        if search_term:
            search_filter = f"%{search_term}%"
            query = query.filter(
                db.or_(
                    Record.title.ilike(search_filter),
                    Record.description.ilike(search_filter),
                    Record.location_name.ilike(search_filter)
                )
            )
        
        query = query.order_by(Record.created_at.desc())
        
        paginated_records = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return make_response({
            'records': [r.to_dict() for r in paginated_records.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': paginated_records.total,
                'pages': paginated_records.pages,
                'has_next': paginated_records.has_next,
                'has_prev': paginated_records.has_prev
            }
        }, 200)
        
    except Exception as e:
        logger.error(f"Failed to fetch user records: {str(e)}")
        return make_response({'error': 'Failed to fetch records'}, 500)

@routes.route('/records/<int:id>', methods=['PATCH'])
@jwt_required()
def update_record(id):
    """Update record (only draft records by owner)"""
    identity = get_jwt_identity()
    
    try:
        record = Record.query.get_or_404(id)

        # Authorization check
        if identity.get('role') != 'user' or record.normal_user_id != identity['id']:
            return make_response({'error': 'Unauthorized'}, 403)
        
        # Only allow editing draft records
        if record.status != 'draft':
            return make_response({'error': 'Only draft records can be edited'}, 400)

        data = request.get_json()
        
        # Validate coordinates if being updated
        if 'latitude' in data or 'longitude' in data:
            lat = data.get('latitude', record.latitude)
            lng = data.get('longitude', record.longitude)
            if (lat is not None or lng is not None) and not validate_coordinates(lat, lng):
                return make_response({'error': 'Invalid coordinates'}, 400)
        
        # Validate media URLs if being updated
        if 'image_url' in data and data['image_url']:
            if not validate_media_url(data['image_url'], 'image'):
                return make_response({'error': 'Invalid image URL'}, 400)
        
        if 'video_url' in data and data['video_url']:
            if not validate_media_url(data['video_url'], 'video'):
                return make_response({'error': 'Invalid video URL'}, 400)
        
        # Update record fields
        if 'title' in data:
            record.title = data['title']
        if 'description' in data:
            record.description = data['description']
        if 'type' in data:
            record.type = data['type']
        if 'latitude' in data:
            record.latitude = data['latitude']
        if 'longitude' in data:
            record.longitude = data['longitude']
        if 'location_name' in data:
            record.location_name = data['location_name']
        if 'urgency_level' in data:
            record.urgency_level = data['urgency_level']
        
        record.updated_at = datetime.utcnow()

        # Update or create media
        if 'image_url' in data or 'video_url' in data:
            media = Media.query.filter_by(record_id=record.id).first()
            if media:
                if 'image_url' in data:
                    media.image_url = data['image_url']
                if 'video_url' in data:
                    media.video_url = data['video_url']
                media.media_url = data.get('image_url') or data.get('video_url')
            else:
                media = Media(
                    record_id=record.id,
                    image_url=data.get('image_url'),
                    video_url=data.get('video_url'),
                    media_type='image' if data.get('image_url') else 'video',
                    media_url=data.get('image_url') or data.get('video_url')
                )
                db.session.add(media)

        db.session.commit()
        
        return make_response({
            'message': 'Record updated successfully',
            'record': record.to_dict()
        }, 200)
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to update record: {str(e)}")
        return make_response({'error': 'Failed to update record'}, 500)

@routes.route('/records/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_record(id):
    """Delete record (only draft records by owner)"""
    identity = get_jwt_identity()
    
    try:
        record = Record.query.get_or_404(id)

        # Authorization check
        if identity.get('role') != 'user' or record.normal_user_id != identity['id']:
            return make_response({'error': 'Unauthorized'}, 403)
        
        # Only allow deleting draft records
        if record.status != 'draft':
            return make_response({'error': 'Only draft records can be deleted'}, 400)

        db.session.delete(record)
        db.session.commit()
        
        return make_response({'message': 'Record deleted successfully'}, 200)
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to delete record: {str(e)}")
        return make_response({'error': 'Failed to delete record'}, 500)

# ------------------ Voting System ------------------

@routes.route('/records/<int:record_id>/vote', methods=['POST'])
@jwt_required()
def vote_record(record_id):
    """Vote/support a record"""
    identity = get_jwt_identity()
    if identity.get('role') != 'user':
        return make_response({'error': 'Only users can vote'}, 403)

    data = request.get_json()
    vote_type = data.get('vote_type', 'support')
    
    if vote_type not in ['support', 'urgent']:
        return make_response({'error': 'Vote type must be "support" or "urgent"'}, 400)

    try:
        record = Record.query.get_or_404(record_id)
        
        # Check if user already voted
        existing_vote = Vote.query.filter_by(
            record_id=record_id,
            user_id=identity['id']
        ).first()
        
        if existing_vote:
            # Update existing vote
            existing_vote.vote_type = vote_type
            message = 'Vote updated successfully'
        else:
            # Create new vote
            new_vote = Vote(
                record_id=record_id,
                user_id=identity['id'],
                vote_type=vote_type
            )
            db.session.add(new_vote)
            message = 'Vote added successfully'
        
        # Update vote count
        vote_count = update_vote_count(record_id)
        
        db.session.commit()
        
        return make_response({
            'message': message,
            'vote_count': vote_count,
            'user_vote': vote_type
        }, 200)
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to vote on record: {str(e)}")
        return make_response({'error': 'Failed to vote on record'}, 500)

@routes.route('/records/<int:record_id>/vote', methods=['DELETE'])
@jwt_required()
def remove_vote(record_id):
    """Remove user's vote from a record"""
    identity = get_jwt_identity()
    if identity.get('role') != 'user':
        return make_response({'error': 'Only users can remove votes'}, 403)

    try:
        vote = Vote.query.filter_by(
            record_id=record_id,
            user_id=identity['id']
        ).first()
        
        if not vote:
            return make_response({'error': 'No vote found to remove'}, 404)
        
        db.session.delete(vote)
        
        # Update vote count
        vote_count = update_vote_count(record_id)
        
        db.session.commit()
        
        return make_response({
            'message': 'Vote removed successfully',
            'vote_count': vote_count
        }, 200)
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to remove vote: {str(e)}")
        return make_response({'error': 'Failed to remove vote'}, 500)

# ------------------ Admin Endpoints ------------------

@routes.route('/admin/records', methods=['GET'])
@jwt_required()
def get_all_records():
    """Get all records (admin only) with enhanced search and filtering"""
    identity = get_jwt_identity()
    if identity.get('role') != 'admin':
        return make_response({'error': 'Only admins can view all records'}, 403)

    try:
        page, per_page = get_pagination_params(request)
        
        # Enhanced filtering
        status_filter = request.args.get('status')
        type_filter = request.args.get('type')
        urgency_filter = request.args.get('urgency')
        user_id_filter = request.args.get('user_id')
        search_term = request.args.get('search', '').strip()
        
        query = Record.query
        
        # Apply filters
        if status_filter and status_filter != 'all':
            query = query.filter(Record.status == status_filter)
        if type_filter and type_filter != 'all':
            query = query.filter(Record.type == type_filter)
        if urgency_filter and urgency_filter != 'all':
            query = query.filter(Record.urgency_level == urgency_filter)
        if user_id_filter:
            try:
                user_id = int(user_id_filter)
                query = query.filter(Record.normal_user_id == user_id)
            except ValueError:
                return make_response({'error': 'Invalid user_id parameter'}, 400)
        
        # Apply search
        if search_term:
            search_filter = f"%{search_term}%"
            query = query.filter(
                db.or_(
                    Record.title.ilike(search_filter),
                    Record.description.ilike(search_filter),
                    Record.location_name.ilike(search_filter)
                )
            )
        
        query = query.order_by(Record.created_at.desc())
        
        paginated_records = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return make_response({
            'records': [r.to_dict() for r in paginated_records.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': paginated_records.total,
                'pages': paginated_records.pages,
                'has_next': paginated_records.has_next,
                'has_prev': paginated_records.has_prev
            }
        }, 200)
        
    except Exception as e:
        logger.error(f"Failed to fetch all records: {str(e)}")
        return make_response({'error': 'Failed to fetch records'}, 500)

@routes.route('/records/<int:id>/status', methods=['PATCH'])
@jwt_required()
def update_status(id):
    """Update record status (admin only)"""
    identity = get_jwt_identity()
    if identity.get('role') != 'admin':
        return make_response({'error': 'Only admins can update status'}, 403)

    try:
        record = Record.query.get_or_404(id)
        data = request.get_json()
        new_status = data.get('status')
        reason = data.get('reason', '')

        if new_status not in ['under-investigation', 'rejected', 'resolved']:
            return make_response({'error': 'Invalid status'}, 400)

        old_status = record.status
        record.status = new_status
        record.updated_at = datetime.utcnow()
        
        # Add resolution notes if provided
        if data.get('resolution_notes'):
            record.resolution_notes = data['resolution_notes']
        
        # Assign admin if not already assigned
        if not record.assigned_admin_id:
            record.assigned_admin_id = identity['id']

        # Create status history
        create_status_history(record.id, old_status, new_status, identity['id'], reason)

        db.session.commit()

        # Send notifications if user exists (not anonymous)
        if record.normal_user_id:
            user = NormalUser.query.get(record.normal_user_id)
            if user:
                # Email notification
                email_message = f"""Hello {user.name},

Your record "{record.title}" has been updated.

Status: {old_status.upper()} ➝ {new_status.upper()}

{f'Reason: {reason}' if reason else ''}

{f'Resolution Notes: {record.resolution_notes}' if record.resolution_notes else ''}

Thank you for using Jiseti!

Best regards,
Jiseti Admin Team"""

                email_sent = send_status_email(user.email, f"Status Update: {record.title}", email_message)
                
                # SMS notification if phone number available
                if user.phone_number:
                    sms_message = f"Jiseti Update: Your report '{record.title}' is now {new_status.upper()}. Check your email for details."
                    send_sms_notification(user.phone_number, sms_message)

        return make_response({
            'message': f'Status updated to {new_status}',
            'record': record.to_dict()
        }, 200)

    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to update status: {str(e)}")
        return make_response({'error': 'Status update failed'}, 500)

@routes.route('/admin/stats', methods=['GET'])
@jwt_required()
def get_admin_stats():
    """Get platform statistics (admin only)"""
    identity = get_jwt_identity()
    if identity.get('role') != 'admin':
        return make_response({'error': 'Only admins can view statistics'}, 403)

    try:
        # Basic counts
        total_records = Record.query.count()
        total_users = NormalUser.query.count()
        
        # Status distribution
        draft_count = Record.query.filter_by(status='draft').count()
        investigation_count = Record.query.filter_by(status='under-investigation').count()
        resolved_count = Record.query.filter_by(status='resolved').count()
        rejected_count = Record.query.filter_by(status='rejected').count()
        
        # Type distribution
        red_flag_count = Record.query.filter_by(type='red-flag').count()
        intervention_count = Record.query.filter_by(type='intervention').count()
        
        # Recent activity (last 30 days)
        from datetime import timedelta
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_records = Record.query.filter(Record.created_at >= thirty_days_ago).count()
        recent_users = NormalUser.query.filter(NormalUser.created_at >= thirty_days_ago).count()
        
        return make_response({
            'total_records': total_records,
            'total_users': total_users,
            'status_distribution': {
                'draft': draft_count,
                'under_investigation': investigation_count,
                'resolved': resolved_count,
                'rejected': rejected_count
            },
            'type_distribution': {
                'red_flag': red_flag_count,
                'intervention': intervention_count
            },
            'recent_activity': {
                'records_last_30_days': recent_records,
                'users_last_30_days': recent_users
            }
        }, 200)
        
    except Exception as e:
        logger.error(f"Failed to fetch admin stats: {str(e)}")
        return make_response({'error': 'Failed to fetch statistics'}, 500)

# ------------------ User Profile ------------------

@routes.route('/user', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current user's information"""
    try:
        identity = get_jwt_identity()
        
        if identity.get('role') == 'user':
            user = NormalUser.query.get(identity['id'])
            if not user:
                return make_response({'error': 'User not found'}, 404)
            
            return make_response(user.to_dict(), 200)
        
        elif identity.get('role') == 'admin':
            admin = Administrator.query.get(identity['id'])
            if not admin:
                return make_response({'error': 'Admin not found'}, 404)
            
            return make_response(admin.to_dict(), 200)
        
        else:
            return make_response({'error': 'Invalid user role'}, 400)
            
    except Exception as e:
        logger.error(f"Error getting current user: {str(e)}")
        return make_response({'error': 'Failed to get user information'}, 500)

@routes.route('/user/profile', methods=['PATCH'])
@jwt_required()
def update_user_profile():
    """Update user profile"""
    identity = get_jwt_identity()
    if identity.get('role') != 'user':
        return make_response({'error': 'Only users can update profile'}, 403)

    try:
        user = NormalUser.query.get(identity['id'])
        if not user:
            return make_response({'error': 'User not found'}, 404)

        data = request.get_json()
        
        # Update allowed fields
        if 'name' in data:
            user.name = data['name']
        if 'phone_number' in data:
            user.phone_number = data['phone_number']
        
        db.session.commit()
        
        return make_response({
            'message': 'Profile updated successfully',
            'user': user.to_dict()
        }, 200)
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to update user profile: {str(e)}")
        return make_response({'error': 'Failed to update profile'}, 500)

# ------------------ Utility Endpoints ------------------

@routes.route('/records/<int:record_id>/history', methods=['GET'])
@jwt_required()
def get_record_history(record_id):
    """Get status history for a record"""
    identity = get_jwt_identity()
    
    try:
        record = Record.query.get_or_404(record_id)
        
        # Authorization check
        if identity.get('role') == 'user' and record.normal_user_id != identity['id']:
            return make_response({'error': 'Unauthorized'}, 403)
        
        history = StatusHistory.query.filter_by(record_id=record_id).order_by(StatusHistory.changed_at.desc()).all()
        
        return make_response({
            'record_id': record_id,
            'history': [h.to_dict() for h in history]
        }, 200)
        
    except Exception as e:
        logger.error(f"Failed to fetch record history: {str(e)}")
        return make_response({'error': 'Failed to fetch record history'}, 500)

# ------------------ Register Blueprint ------------------

def register_routes(app):
    app.register_blueprint(routes)
