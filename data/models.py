import os
from datetime import datetime
from dotenv import load_dotenv

from sqlalchemy import (
    Boolean,
    DateTime,
    BigInteger,
    ForeignKey,
    Integer,
    String,
    select,
    Float,
    Text
)
from sqlalchemy.ext.asyncio import (
    AsyncAttrs,
    AsyncEngine,
    create_async_engine,
    AsyncSession
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    sessionmaker
)

load_dotenv()

database_url = os.getenv("DATABASE_URL")
if not database_url:
    raise ValueError("DATABASE_URL is not set in the environment variables")

engine: AsyncEngine = create_async_engine(database_url)

async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

class Base(AsyncAttrs, DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[BigInteger] = mapped_column(BigInteger, unique=True, nullable=False)
    referral_code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    referrer_id: Mapped[BigInteger] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(), nullable=False)

class StarPackage(Base):
    __tablename__ = "star_packages"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    stars_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

class Transaction(Base):
    __tablename__ = "transactions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[BigInteger] = mapped_column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    package_id: Mapped[int] = mapped_column(Integer, ForeignKey("star_packages.id"), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # pending, completed, failed
    payment_method: Mapped[str] = mapped_column(String(50), nullable=False)
    payment_id: Mapped[str] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(), nullable=False)

class Support(Base):
    __tablename__ = "support_tickets"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[BigInteger] = mapped_column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    subject: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # open, closed, in_progress
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(), nullable=False)
    
async def async_main():
    try:
        async with engine.begin() as conn:
            tables = await conn.run_sync(lambda sync_conn: sync_conn.dialect.get_table_names(sync_conn))
            
            required_tables = {cls.__tablename__ for cls in Base.__subclasses__()}
            
            missing_tables = required_tables - set(tables)
            
            if missing_tables:
                print(f"⚠️ Missing tables: {', '.join(missing_tables)}")
                for table in Base.metadata.sorted_tables:
                    if table.name in missing_tables:
                        await conn.run_sync(lambda sync_conn: table.create(sync_conn))
                print("Missing tables are created")
            else:
                print("DB is ready to work")
    except Exception as e:
        print(f"❌ Error in DB initialization: {str(e)}")
        raise e