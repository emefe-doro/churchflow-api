import asyncio

from sqlalchemy import select

from app.database import async_session
from app.models.church import Church, Branch
from app.models.contact import Contact
from app.models.message_template import MessageTemplate
from app.models.user import Role, User

SEED_TEMPLATES = [
    {
        "name": "First Timer Welcome",
        "category": "first_timer",
        "channel": "whatsapp",
        "body": "Hello {name}, thank you for worshipping with us at {church_name}. We were blessed to have you. We pray that God strengthens and guides you. We would love to see you again in our next service.",
        "approved": True,
    },
    {
        "name": "First Timer Follow-Up",
        "category": "first_timer",
        "channel": "whatsapp",
        "body": "Hello {name}, we just wanted to check on you and thank you again for visiting {church_name}. We hope you were blessed by the service. Please let us know if you need prayer or any information.",
        "approved": True,
    },
    {
        "name": "New Convert Welcome",
        "category": "new_convert",
        "channel": "whatsapp",
        "body": "Hello {name}, congratulations on your decision to follow Christ. This is the beginning of a beautiful journey with God. We are praying for you and would love to support you as you grow in faith.",
        "approved": True,
    },
    {
        "name": "Foundation Class Invite",
        "category": "new_convert",
        "channel": "whatsapp",
        "body": "Hello {name}, we would like to invite you to our foundation class where you can learn more about your new life in Christ. Please let us know if you will be available.",
        "approved": True,
    },
    {
        "name": "Outreach Follow-Up",
        "category": "outreach",
        "channel": "whatsapp",
        "body": "Hello {name}, greetings from {church_name}. We met you during our outreach at {location}. We are praying for you and would love to invite you to join us in our next service.",
        "approved": True,
    },
    {
        "name": "Service Unit Reminder",
        "category": "service_unit",
        "channel": "whatsapp",
        "body": "Good day team, this is a reminder for our {unit_name} assignment on {date}. Please let us prepare and be punctual. Thank you for your commitment and service.",
        "approved": True,
    },
    {
        "name": "General Pastoral Greeting",
        "category": "general",
        "channel": "whatsapp",
        "body": "Hello {name}, warm greetings from {church_name}. We are thinking of you and praying for you. If there is anything you need, please do not hesitate to reach out to us. God bless you.",
        "approved": True,
    },
]

SEED_CONTACTS = [
    {"first_name": "Oghenedoro", "last_name": "Emefe", "phone": "+2347065510101", "category": "first_timer", "source": "service", "gender": "male", "age_group": "young_adult", "consent_given": True, "assigned_worker_id": 1},
    {"first_name": "Abena", "last_name": "Asare", "phone": "+233502345678", "category": "first_timer", "source": "service", "gender": "female", "age_group": "adult", "consent_given": True},
    {"first_name": "Kofi", "last_name": "Appiah", "phone": "+233503456789", "category": "new_convert", "source": "service", "gender": "male", "age_group": "young_adult", "consent_given": True},
    {"first_name": "Ama", "last_name": "Owusu", "phone": "+233504567890", "category": "new_convert", "source": "referral", "gender": "female", "age_group": "teen", "consent_given": True},
    {"first_name": "Yaw", "last_name": "Boateng", "phone": "+233505678901", "category": "outreach_convert", "source": "outreach", "gender": "male", "age_group": "adult", "consent_given": True, "notes": "Met during outreach at Nima Market"},
    {"first_name": "Efua", "last_name": "Dankwa", "phone": "+233506789012", "category": "outreach_convert", "source": "outreach", "gender": "female", "age_group": "young_adult", "consent_given": True, "notes": "Met during outreach at Madina Central"},
    {"first_name": "Kwame", "last_name": "Nkrumah", "phone": "+233507890123", "category": "member", "source": "service", "gender": "male", "age_group": "senior", "consent_given": True},
    {"first_name": "Akua", "last_name": "Manu", "phone": "+233508901234", "category": "first_timer", "source": "online", "gender": "female", "age_group": "adult", "consent_given": True},
    {"first_name": "Kwesi", "last_name": "Arthur", "phone": "+233509012345", "category": "new_convert", "source": "referral", "gender": "male", "age_group": "young_adult", "consent_given": True},
    {"first_name": "Adwoa", "last_name": "Sarpong", "phone": "+233509876543", "category": "other", "source": "other", "gender": "female", "age_group": "adult", "consent_given": False, "opt_out": True},
]


async def seed():
    async with async_session() as db:
        async with db.begin():
            await _seed_church(db)
            await _seed_branch(db)
            await _seed_role(db)
            await _seed_user(db)
            await _seed_contacts(db)
            await _seed_templates(db)
        print("Seed complete.")


async def _seed_church(db):
    existing = (await db.execute(select(Church).where(Church.id == 1))).scalar_one_or_none()
    if existing:
        print("Church already exists (id=1), skipping.")
        return
    church = Church(
        id=1,
        name="Potter Tabernacle Ministry",
        address="Blackgate Badore Ajah, Lagos",
        phone="+2347065510101",
        email="info@potters.org",
    )
    db.add(church)
    await db.flush()
    print("Created Church: Potter Tabernacle Ministry (id=1)")


async def _seed_branch(db):
    existing = (await db.execute(select(Branch).where(Branch.id == 1))).scalar_one_or_none()
    if existing:
        print("Branch already exists (id=1), skipping.")
        return
    branch = Branch(
        id=1,
        church_id=1,
        name="Main Branch Blackgate Badore Ajah",
        location="Blackgate, Badore, Ajah, Lagos",
    )
    db.add(branch)
    await db.flush()
    print("Created Branch: Main Branch Blackgate Badore Ajah (id=1)")


async def _seed_role(db):
    existing = (await db.execute(select(Role).where(Role.id == 1))).scalar_one_or_none()
    if existing:
        print("Role already exists (id=1), skipping.")
        return
    role = Role(
        id=1,
        name="Admin",
        description="Full system access",
    )
    db.add(role)
    await db.flush()
    print("Created Role: Admin (id=1)")


async def _seed_user(db):
    existing = (await db.execute(select(User).where(User.id == 1))).scalar_one_or_none()
    if existing:
        print("User already exists (id=1), skipping.")
        return
    user = User(
        id=1,
        church_id=1,
        branch_id=1,
        role_id=1,
        name="Pastor Yinka",
        email="pastoryinka@pottertabernacle.org",
        phone="+2347065510101",
        hashed_password=None,
        active=True,
    )
    db.add(user)
    await db.flush()
    print("Created User: Pastor Yinka (id=1)")


async def _seed_contacts(db):
    existing = (await db.execute(select(Contact).where(Contact.church_id == 1))).scalars().first()
    if existing:
        print(f"Contacts already exist for church_id=1, skipping.")
        return

    for i, c in enumerate(SEED_CONTACTS, start=1):
        contact = Contact(
            id=i,
            church_id=1,
            branch_id=1,
            first_name=c["first_name"],
            last_name=c["last_name"],
            phone=c["phone"],
            category=c["category"],
            source=c["source"],
            gender=c.get("gender"),
            age_group=c.get("age_group"),
            notes=c.get("notes"),
            consent_given=c["consent_given"],
            opt_out=c.get("opt_out", False),
            assigned_worker_id=c.get("assigned_worker_id"),
            status="new",
        )
        db.add(contact)

    await db.flush()
    print(f"Created {len(SEED_CONTACTS)} contacts")


async def _seed_templates(db):
    existing = (await db.execute(select(MessageTemplate).where(MessageTemplate.church_id == 1))).scalars().first()
    if existing:
        print(f"Templates already exist for church_id=1, skipping.")
        return

    for i, t in enumerate(SEED_TEMPLATES, start=1):
        template = MessageTemplate(
            id=i,
            church_id=1,
            branch_id=1,
            name=t["name"],
            category=t["category"],
            channel=t["channel"],
            body=t["body"],
            approved=t["approved"],
            created_by=1,
        )
        db.add(template)

    await db.flush()
    print(f"Created {len(SEED_TEMPLATES)} approved message templates")


if __name__ == "__main__":
    asyncio.run(seed())
