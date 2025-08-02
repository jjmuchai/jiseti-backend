# seed.py - Comprehensive Database Seeding for Jiseti
import os
import random
from datetime import datetime, timedelta
from faker import Faker
from werkzeug.security import generate_password_hash
from app import create_app
from models import db, NormalUser, Administrator, Record, Media, Vote, StatusHistory, Notification

# Initialize Faker for generating realistic data
fake = Faker()

# Helper function to get past dates
def get_past_date(days_ago):
    """Get a date from X days ago"""
    return datetime.utcnow() - timedelta(days=days_ago)

def get_random_past_date(min_days, max_days):
    """Get a random date between min_days and max_days ago"""
    days_ago = random.randint(min_days, max_days)
    return datetime.utcnow() - timedelta(days=days_ago)

def clear_database():
    """Clear all existing data"""
    print("🗑️  Clearing existing data...")
    
    # Delete in correct order due to foreign key constraints
    Vote.query.delete()
    StatusHistory.query.delete()
    Notification.query.delete()
    Media.query.delete()
    Record.query.delete()
    Administrator.query.delete()
    NormalUser.query.delete()
    
    db.session.commit()
    print("✅ Database cleared successfully!")

def create_users():
    """Create diverse normal users"""
    print("👤 Creating normal users...")
    
    users = []
    
    # Predefined users for consistent testing
    predefined_users = [
        {"name": "Alice Wanjiku", "email": "alice.wanjiku@gmail.com"},
        {"name": "John Mutua", "email": "john.mutua@gmail.com"},
        {"name": "Grace Achieng", "email": "grace.achieng@gmail.com"},
        {"name": "Peter Kiprotich", "email": "peter.kiprotich@gmail.com"},
        {"name": "Mary Njeri", "email": "mary.njeri@gmail.com"},
        {"name": "David Otieno", "email": "david.otieno@gmail.com"},
        {"name": "Sarah Wanjiru", "email": "sarah.wanjiru@gmail.com"},
        {"name": "Michael Kimani", "email": "michael.kimani@gmail.com"},
        {"name": "Faith Muthoni", "email": "faith.muthoni@gmail.com"},
        {"name": "James Ochieng", "email": "james.ochieng@gmail.com"},
    ]
    
    # Create predefined users
    for user_data in predefined_users:
        user = NormalUser(
            name=user_data["name"],
            email=user_data["email"],
            password=generate_password_hash("password123"),
            phone_number=f"+254{random.randint(700000000, 799999999)}",
            is_active=True,
            email_verified=random.choice([True, False]),
            created_at=get_random_past_date(1, 180)  # 1-180 days ago
        )
        users.append(user)
        db.session.add(user)
    
    # Create additional random users
    for i in range(15):
        user = NormalUser(
            name=fake.name(),
            email=f"{fake.user_name()}{random.randint(1, 999)}@gmail.com",
            password=generate_password_hash("password123"),
            phone_number=f"+254{random.randint(700000000, 799999999)}",
            is_active=random.choice([True, True, True, False]),  # 75% active
            email_verified=random.choice([True, False]),
            created_at=get_random_past_date(30, 365)  # 30-365 days ago
        )
        users.append(user)
        db.session.add(user)
    
    db.session.commit()
    print(f"✅ Created {len(users)} normal users")
    return users

def create_administrators():
    """Create administrator accounts"""
    print("👨‍💼 Creating administrators...")
    
    admins = []
    
    # Default admin (if not exists)
    if not Administrator.query.filter_by(email="admin@jiseti.go.ke").first():
        default_admin = Administrator(
            name="System Administrator",
            email="admin@jiseti.go.ke",
            password=generate_password_hash("admin123"),
            admin_number="ADM-DEFAULT-001",
            role="admin",
            created_at=datetime.utcnow() - timedelta(days=365),
            last_login=datetime.utcnow() - timedelta(hours=2)
        )
        admins.append(default_admin)
        db.session.add(default_admin)
    
    # Additional administrators
    admin_data = [
        {"name": "Catherine Kariuki", "email": "catherine.kariuki@jiseti.go.ke"},
        {"name": "Robert Mwangi", "email": "robert.mwangi@jiseti.go.ke"},
        {"name": "Diana Chebet", "email": "diana.chebet@jiseti.go.ke"},
        {"name": "Samuel Ndungu", "email": "samuel.ndungu@jiseti.go.ke"},
    ]
    
    for i, admin_info in enumerate(admin_data, 2):
        admin = Administrator(
            name=admin_info["name"],
            email=admin_info["email"],
            password=generate_password_hash("admin123"),
            admin_number=f"ADM-{str(i).zfill(3)}-{random.randint(100, 999)}",
            role="admin",
            created_at=get_random_past_date(365, 730),  # 1-2 years ago
            last_login=get_random_past_date(1, 7)  # 1-7 days ago
        )
        admins.append(admin)
        db.session.add(admin)
    
    db.session.commit()
    print(f"✅ Created {len(admins)} administrators")
    return admins

def create_records(users, admins):
    """Create diverse corruption and intervention records"""
    print("📋 Creating records...")
    
    records = []
    
    # Kenyan cities coordinates for realistic locations
    kenyan_locations = [
        {"name": "Nairobi CBD", "lat": -1.2921, "lng": 36.8219},
        {"name": "Mombasa", "lat": -4.0435, "lng": 39.6682},
        {"name": "Kisumu", "lat": -0.0917, "lng": 34.7680},
        {"name": "Nakuru", "lat": -0.3031, "lng": 36.0800},
        {"name": "Eldoret", "lat": 0.5143, "lng": 35.2698},
        {"name": "Machakos", "lat": -1.5177, "lng": 37.2634},
        {"name": "Meru", "lat": 0.0467, "lng": 37.6556},
        {"name": "Thika", "lat": -1.0332, "lng": 37.0692},
        {"name": "Kitale", "lat": 1.0157, "lng": 35.0062},
        {"name": "Malindi", "lat": -3.2194, "lng": 40.1169},
    ]
    
    # Red-flag (corruption) records
    red_flag_titles = [
        "Police officer demanding bribes at roadblock",
        "Hospital staff requesting payment for free services",
        "County official soliciting kickbacks for permits",
        "Teacher selling exam papers to students",
        "Traffic officer taking bribes to ignore violations",
        "Government clerk demanding extra fees for services",
        "Hospital administrator inflating medical bills",
        "Municipal officer demanding bribes for licenses",
        "Police station demanding money for case files",
        "School headteacher embezzling lunch program funds",
        "County treasury official misappropriating funds",
        "Hospital pharmacist selling donated medicines",
        "Traffic department issuing fake driving licenses",
        "Land office official demanding bribes for titles",
        "Water department officer taking money for connections"
    ]
    
    red_flag_descriptions = [
        "A police officer at the Mombasa Road checkpoint is systematically demanding 500 KSH from drivers to avoid 'inspection'. This happens daily between 8AM-10AM.",
        "Nurses at Kenyatta Hospital are asking patients to pay 1000 KSH for bed sheets and basic care that should be free under universal healthcare.",
        "The county licensing officer is demanding 50,000 KSH under the table to approve business permits that normally cost 5,000 KSH.",
        "Mathematics teacher at Moi High School is selling KCSE examination papers to students for 10,000 KSH each.",
        "Traffic officers along Uhuru Highway are taking 2,000 KSH bribes to ignore overloaded vehicles and safety violations.",
        "The registrar at Huduma Centre is demanding extra 3,000 KSH for 'expedited processing' of national ID applications.",
        "The medical superintendent is inflating patient bills by 300% and pocketing the difference, especially for insurance claims.",
        "Municipal council officers are demanding 15,000 KSH bribes to approve building plans that meet all requirements.",
        "Police officers at Central Police Station are demanding 5,000 KSH to open criminal case files and investigate crimes.",
        "The school principal has been diverting lunch program funds meant for 500 students to personal accounts for 6 months.",
        "County treasury official has been inflating supplier invoices and keeping 40% of public procurement funds.",
        "Hospital pharmacy staff are selling ARV drugs and other donated medicines to private clinics at full price.",
        "Driving test examiners are issuing licenses without proper testing for payments of 20,000 KSH per license.",
        "Land registry officials are demanding 100,000 KSH bribes to process legitimate land title transfers.",
        "Water company technicians are installing illegal connections and charging residents 25,000 KSH each."
    ]
    
    # Intervention records
    intervention_titles = [
        "Collapsed bridge blocking main road to market",
        "Broken water pipes flooding residential area",
        "Non-functional street lights causing accidents",
        "Overflowing sewage system in estate",
        "Damaged school roof endangering students",
        "Blocked drainage causing flooding during rains",
        "Broken ambulance at health center",
        "Collapsed classroom ceiling at primary school",
        "Faulty traffic lights causing accidents",
        "Contaminated water supply in village",
        "Damaged road making area inaccessible",
        "Non-functional fire station equipment",
        "Broken fence allowing livestock into crops",
        "Malfunctioning hospital generator",
        "Damaged library roof leaking on books"
    ]
    
    intervention_descriptions = [
        "The main bridge connecting our village to the market collapsed last week. Over 5,000 residents cannot access essential services. Heavy rains washed away the temporary wooden bridge.",
        "Water pipes burst on Kenyatta Avenue, flooding 20 homes and making the road impassable. Families have been without clean water for 3 days.",
        "All street lights on University Way have been non-functional for 2 months. There have been 3 accidents and increased criminal activity after dark.",
        "The sewage system in Umoja Estate has been overflowing for weeks. Raw sewage is flowing into homes and creating health hazards for 500 families.",
        "The roof of Harambee Primary School classroom collapsed, injuring 5 students. 200 students cannot attend classes due to safety concerns.",
        "Storm drains on Tom Mboya Street are completely blocked with garbage. The street floods heavily during rains, damaging businesses.",
        "The only ambulance at Machakos Health Center has been broken for 3 months. Patients requiring emergency transport have to use private vehicles.",
        "The ceiling of Class 8 at St. Mary's Primary collapsed during heavy rains. 45 students are now learning under a tree.",
        "Traffic lights at Nyerere Road junction have been malfunctioning for weeks. There have been 4 accidents and massive traffic jams daily.",
        "The borehole supplying water to Kibera village is contaminated with sewage. Over 1,000 residents are at risk of waterborne diseases.",
        "The access road to Kiambu village is completely damaged by heavy rains. Sick people cannot reach the hospital, and food supplies cannot get in.",
        "The fire station's main truck has been out of service for 6 months. There have been 3 house fires with no proper emergency response.",
        "The perimeter fence of the government agricultural station is completely broken. Local livestock are destroying research crops worth millions.",
        "The backup generator at District Hospital failed during the last power outage. Patients in ICU and surgery were at serious risk.",
        "The public library roof has been leaking for months. Hundreds of books and computers are damaged, affecting education for local students."
    ]
    
    # Create red-flag records
    for i in range(len(red_flag_titles)):
        location = random.choice(kenyan_locations)
        
        # Add some variation to coordinates
        lat_variation = random.uniform(-0.01, 0.01)
        lng_variation = random.uniform(-0.01, 0.01)
        
        created_date = get_random_past_date(1, 90)  # 1-90 days ago
        
        record = Record(
            type="red-flag",
            title=red_flag_titles[i],
            description=red_flag_descriptions[i] if i < len(red_flag_descriptions) else fake.text(max_nb_chars=300),
            status=random.choices(
                ['draft', 'under-investigation', 'resolved', 'rejected'],
                weights=[20, 40, 30, 10]  # More likely to be under investigation
            )[0],
            latitude=location["lat"] + lat_variation,
            longitude=location["lng"] + lng_variation,
            location_name=location["name"],
            urgency_level=random.choices(
                ['low', 'medium', 'high', 'critical'],
                weights=[15, 40, 35, 10]
            )[0],
            is_anonymous=random.choice([True, False]),
            vote_count=0,  # Will be updated after creating votes
            normal_user_id=random.choice(users).id if random.random() > 0.2 else None,  # 20% anonymous
            assigned_admin_id=random.choice(admins).id if random.random() > 0.3 else None,  # 70% assigned
            created_at=created_date,
            updated_at=created_date + timedelta(hours=random.randint(1, 72))
        )
        
        records.append(record)
        db.session.add(record)
    
    # Create intervention records
    for i in range(len(intervention_titles)):
        location = random.choice(kenyan_locations)
        
        lat_variation = random.uniform(-0.01, 0.01)
        lng_variation = random.uniform(-0.01, 0.01)
        
        created_date = get_random_past_date(1, 60)  # 1-60 days ago
        
        record = Record(
            type="intervention",
            title=intervention_titles[i],
            description=intervention_descriptions[i] if i < len(intervention_descriptions) else fake.text(max_nb_chars=300),
            status=random.choices(
                ['draft', 'under-investigation', 'resolved', 'rejected'],
                weights=[25, 45, 25, 5]  # Interventions less likely to be rejected
            )[0],
            latitude=location["lat"] + lat_variation,
            longitude=location["lng"] + lng_variation,
            location_name=location["name"],
            urgency_level=random.choices(
                ['low', 'medium', 'high', 'critical'],
                weights=[10, 30, 40, 20]  # Interventions often more urgent
            )[0],
            is_anonymous=random.choice([True, False]),
            vote_count=0,  # Will be updated after creating votes
            normal_user_id=random.choice(users).id if random.random() > 0.15 else None,  # 15% anonymous
            assigned_admin_id=random.choice(admins).id if random.random() > 0.2 else None,  # 80% assigned
            created_at=created_date,
            updated_at=created_date + timedelta(hours=random.randint(1, 48))
        )
        
        records.append(record)
        db.session.add(record)
    
    # Add a few more random records
    for _ in range(10):
        location = random.choice(kenyan_locations)
        
        record = Record(
            type=random.choice(["red-flag", "intervention"]),
            title=fake.sentence(nb_words=6),
            description=fake.text(max_nb_chars=400),
            status=random.choices(
                ['draft', 'under-investigation', 'resolved', 'rejected'],
                weights=[20, 40, 30, 10]
            )[0],
            latitude=location["lat"] + random.uniform(-0.02, 0.02),
            longitude=location["lng"] + random.uniform(-0.02, 0.02),
            location_name=location["name"],
            urgency_level=random.choice(['low', 'medium', 'high', 'critical']),
            is_anonymous=random.choice([True, False]),
            vote_count=0,
            normal_user_id=random.choice(users).id if random.random() > 0.3 else None,
            assigned_admin_id=random.choice(admins).id if random.random() > 0.4 else None,
            created_at=get_random_past_date(1, 30)  # 1-30 days ago
        )
        
        records.append(record)
        db.session.add(record)
    
    db.session.commit()
    print(f"✅ Created {len(records)} records")
    return records

def create_media(records):
    """Create media attachments for records"""
    print("📷 Creating media attachments...")
    
    media_items = []
    
    # Sample image and video URLs for demonstration
    sample_images = [
        "https://images.unsplash.com/photo-1590736969955-71cc94901144?w=800",  # Road
        "https://images.unsplash.com/photo-1581833971358-2c8b550f87b3?w=800",  # Hospital
        "https://images.unsplash.com/photo-1541888946425-d81bb19240f5?w=800",  # Office
        "https://images.unsplash.com/photo-1562774053-701939374585?w=800",  # School
        "https://images.unsplash.com/photo-1556075798-4825dfaaf498?w=800",  # Bridge
        "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=800",  # Police
        "https://images.unsplash.com/photo-1576091160399-112ba8d25d1f?w=800",  # Water
        "https://images.unsplash.com/photo-1582213782179-e0d53f98f2ca?w=800",  # Street
        "https://images.unsplash.com/photo-1551218808-94e220e084d2?w=800",  # Building
        "https://images.unsplash.com/photo-1558618047-3c8c76ca7d13?w=800",  # Traffic
    ]
    
    sample_videos = [
        "https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4",
        "https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_2mb.mp4",
    ]
    
    # Add media to about 60% of records
    for record in random.sample(records, int(len(records) * 0.6)):
        # Some records have both image and video
        if random.random() < 0.7: 
            image_url = random.choice(sample_images)
            media = Media(
                record_id=record.id,
                media_type="image",
                media_url=image_url,
                image_url=image_url,  
                filename=f"evidence_{record.id}_{random.randint(1000, 9999)}.jpg",
                file_size=random.randint(500000, 3000000),  
                uploaded_at=record.created_at + timedelta(minutes=random.randint(5, 120))
            )
            media_items.append(media)
            db.session.add(media)
        
        if random.random() < 0.2:  
            video_url = random.choice(sample_videos)
            media = Media(
                record_id=record.id,
                media_type="video", 
                media_url=video_url,
                video_url=video_url,  
                filename=f"evidence_{record.id}_{random.randint(1000, 9999)}.mp4",
                file_size=random.randint(5000000, 50000000),  
                uploaded_at=record.created_at + timedelta(minutes=random.randint(10, 180))
            )
            media_items.append(media)
            db.session.add(media)
    
    db.session.commit()
    print(f"✅ Created {len(media_items)} media attachments")
    return media_items

def create_votes(records, users):
    """Create user votes on records"""
    print("🗳️  Creating votes...")
    
    votes = []
    
    # Only create votes for non-draft records
    public_records = [r for r in records if r.status != 'draft']
    
    for record in public_records:
        # Random number of votes per record
        num_votes = random.choices(
            [0, 1, 2, 3, 4, 5, 10, 15, 20],
            weights=[10, 15, 20, 20, 15, 10, 5, 3, 2]
        )[0]
        
        # Select random users to vote
        voting_users = random.sample(users, min(num_votes, len(users)))
        
        for user in voting_users:
            vote = Vote(
                record_id=record.id,
                user_id=user.id,
                vote_type=random.choices(['support', 'urgent'], weights=[70, 30])[0],
                created_at=get_random_past_date(
                    0, 
                    (datetime.utcnow() - record.created_at).days
                ) if record.created_at else get_random_past_date(1, 30)
            )
            votes.append(vote)
            db.session.add(vote)
    
    db.session.commit()
    
    # Update vote counts on records
    for record in records:
        record.vote_count = Vote.query.filter_by(record_id=record.id).count()
    
    db.session.commit()
    print(f"✅ Created {len(votes)} votes")
    return votes

def create_status_history(records, admins):
    """Create status change history"""
    print("📊 Creating status history...")
    
    histories = []
    
    for record in records:
        if record.status != 'draft':
            # Create history for status changes
            statuses = ['draft', 'under-investigation']
            
            if record.status in ['resolved', 'rejected']:
                statuses.append(record.status)
            
            for i, status in enumerate(statuses):
                if i == 0:
                    # Initial creation
                    continue
                
                old_status = statuses[i-1] if i > 0 else None
                
                history = StatusHistory(
                    record_id=record.id,
                    old_status=old_status,
                    new_status=status,
                    changed_by=random.choice(admins).id if record.assigned_admin_id else None,
                    change_reason=random.choice([
                        "Escalated for investigation",
                        "Evidence reviewed and validated", 
                        "Investigation completed",
                        "Additional evidence required",
                        "Case resolved satisfactorily",
                        "Insufficient evidence to proceed",
                        "Duplicate report identified"
                    ]),
                    changed_at=record.created_at + timedelta(
                        hours=random.randint(1, 72 * i)
                    )
                )
                histories.append(history)
                db.session.add(history)
    
    db.session.commit()
    print(f"✅ Created {len(histories)} status history entries")
    return histories

def create_notifications(records, users):
    """Create notification logs"""
    print("📧 Creating notification logs...")
    
    notifications = []
    
    # Create notifications for status changes
    for record in records:
        if record.normal_user_id and record.status != 'draft':
            # Email notification
            email_notification = Notification(
                record_id=record.id,
                user_id=record.normal_user_id,
                notification_type="email",
                message=f"Your report '{record.title}' status has been updated to {record.status}",
                sent_at=record.updated_at,
                delivery_status=random.choices(
                    ['sent', 'failed'], 
                    weights=[95, 5]  
                )[0],
                external_id=f"sg_{random.randint(100000, 999999)}"
            )
            notifications.append(email_notification)
            db.session.add(email_notification)
            
            # SMS notification (if user has phone)
            user = next((u for u in users if u.id == record.normal_user_id), None)
            if user and user.phone_number and random.random() < 0.6:  # 60% have SMS
                sms_notification = Notification(
                    record_id=record.id,
                    user_id=record.normal_user_id,
                    notification_type="sms",
                    message=f"Jiseti: Your report '{record.title[:30]}...' is now {record.status.upper()}",
                    sent_at=record.updated_at + timedelta(minutes=5),
                    delivery_status=random.choices(
                        ['sent', 'failed'],
                        weights=[90, 10]  
                    )[0],
                    external_id=f"tw_{random.randint(100000, 999999)}"
                )
                notifications.append(sms_notification)
                db.session.add(sms_notification)
    
    db.session.commit()
    print(f"✅ Created {len(notifications)} notification logs")
    return notifications

def print_summary():
    """Print database summary"""
    print("\n" + "="*60)
    print("📊 DATABASE SEEDING SUMMARY")
    print("="*60)
    
    # Count records
    total_users = NormalUser.query.count()
    active_users = NormalUser.query.filter_by(is_active=True).count()
    total_admins = Administrator.query.count()
    total_records = Record.query.count()
    red_flags = Record.query.filter_by(type='red-flag').count()
    interventions = Record.query.filter_by(type='intervention').count()
    
    # Status distribution
    draft_count = Record.query.filter_by(status='draft').count()
    investigation_count = Record.query.filter_by(status='under-investigation').count()
    resolved_count = Record.query.filter_by(status='resolved').count()
    rejected_count = Record.query.filter_by(status='rejected').count()
    
    # Other counts
    total_votes = Vote.query.count()
    total_media = Media.query.count()
    total_notifications = Notification.query.count()
    
    print(f"👥 Users: {total_users} total ({active_users} active)")
    print(f"👨‍💼 Administrators: {total_admins}")
    print(f"📋 Records: {total_records} total")
    print(f"   🚩 Red-flags: {red_flags}")
    print(f"   🏛️  Interventions: {interventions}")
    print(f"\n📊 Status Distribution:")
    print(f"   📝 Draft: {draft_count}")
    print(f"   🔍 Under Investigation: {investigation_count}")
    print(f"   ✅ Resolved: {resolved_count}")
    print(f"   ❌ Rejected: {rejected_count}")
    print(f"\n🗳️  Votes: {total_votes}")
    print(f"📷 Media Attachments: {total_media}")
    print(f"📧 Notifications: {total_notifications}")
    
    print(f"\n🔑 Test Accounts Created:")
    print(f"   👤 User: alice.wanjiku@gmail.com / password123")
    print(f"   👤 User: john.mutua@gmail.com / password123")
    print(f"   👨‍💼 Admin: admin@jiseti.go.ke / admin123")
    print(f"   👨‍💼 Admin: catherine.kariuki@jiseti.go.ke / admin123")
    
    print(f"\n🌍 Sample Locations Used:")
    print(f"   📍 Nairobi, Mombasa, Kisumu, Nakuru, Eldoret")
    print(f"   📍 Machakos, Meru, Thika, Kitale, Malindi")
    
    print("\n" + "="*60)
    print("✅ DATABASE SEEDING COMPLETED SUCCESSFULLY!")
    print("🚀 Ready for testing and demonstration")
    print("="*60)

def seed_database():
    """Main seeding function"""
    print("🌱 Starting database seeding...")
    print("This will create realistic test data for Jiseti platform")
    print("-" * 60)
    
    try:
        # Clear existing data
        clear_database()
        
        # Create data in order
        users = create_users()
        admins = create_administrators()
        records = create_records(users, admins)
        media_items = create_media(records)
        votes = create_votes(records, users)
        histories = create_status_history(records, admins)
        notifications = create_notifications(records, users)
        
        # Print summary
        print_summary()
        
        # Additional helpful info
        print(f"\n🔗 API Testing URLs:")
        print(f"   Health: http://localhost:5000/health")
        print(f"   Public Records: http://localhost:5000/public/records")
        print(f"   Admin Stats: http://localhost:5000/admin/stats (requires auth)")
        
    except Exception as e:
        print(f"❌ Error during seeding: {e}")
        db.session.rollback()
        raise

if __name__ == "__main__":
    app = create_app()
    
    with app.app_context():
        # Check if Faker is installed
        try:
            import faker
        except ImportError:
            print("❌ Faker not installed. Installing...")
            os.system("pip install faker")
            print("✅ Faker installed successfully!")
        
        # Confirm before seeding
        print("⚠️  This will clear all existing data and create new test data.")
        confirm = input("Continue? (y/N): ").lower().strip()
        
        if confirm in ['y', 'yes']:
            seed_database()
        else:
            print("❌ Seeding cancelled.")
