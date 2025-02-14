from typing import Optional, List
from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

from .models import User, StarPackage, Transaction, Support, async_session

#region User methods
async def create_user(
    telegram_id: int,
    referral_code: str,
    referrer_id: Optional[int] = None
) -> User:
    async with async_session() as session:
        try:
            user = User(
                telegram_id=telegram_id,
                referral_code=referral_code,
                referrer_id=referrer_id
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user
        except Exception as e:
            print(f"Ошибка при создании пользователя: {e}")
            raise e

async def get_user_by_telegram_id(
    telegram_id: int
) -> Optional[User]:
    async with async_session() as session:
        query = select(User).where(User.telegram_id == telegram_id)
        result = await session.execute(query)
        return result.scalar_one_or_none()

async def get_user_by_referral_code(
    referral_code: str
) -> Optional[User]:
    async with async_session() as session:
        query = select(User).where(User.referral_code == referral_code)
        result = await session.execute(query)
        return result.scalar_one_or_none()

#endregion

#region StarPackage methods
async def create_star_package(
    stars_amount: int,
    price: float,
    description: Optional[str] = None,
    is_active: bool = True
) -> StarPackage:
    async with async_session() as session:
        try:
            package = StarPackage(
                stars_amount=stars_amount,
                price=price,
                description=description,
                is_active=is_active
            )
            session.add(package)
            await session.commit()
            await session.refresh(package)
            return package
        except Exception as e:
            print(f"Ошибка при создании пакета: {e}")
            raise e

async def get_active_star_packages() -> List[StarPackage]:
    async with async_session() as session:
        query = select(StarPackage).where(StarPackage.is_active == True)
        result = await session.execute(query)
        return list(result.scalars().all())

async def get_star_package_by_id(
    package_id: int
) -> Optional[StarPackage]:
    async with async_session() as session:
        query = select(StarPackage).where(StarPackage.id == package_id)
        result = await session.execute(query)
        return result.scalar_one_or_none()

#endregion

#region Transaction methods
async def create_transaction(
    user_id: int,
    package_id: int,
    amount: float,
    payment_method: str,
    payment_id: Optional[str] = None,
    status: str = "pending"
) -> Transaction:
    async with async_session() as session:
        try:
            transaction = Transaction(
                user_id=user_id,
                package_id=package_id,
                amount=amount,
                payment_method=payment_method,
                payment_id=payment_id,
                status=status
            )
            session.add(transaction)
            await session.commit()
            await session.refresh(transaction)
            return transaction
        except Exception as e:
            print(f"Ошибка при создании транзакции: {e}")
            raise e

async def update_transaction_status(
    transaction_id: int,
    status: str
) -> Optional[Transaction]:
    async with async_session() as session:
        stmt = (
            update(Transaction)
            .where(Transaction.id == transaction_id)
            .values(status=status)
            .returning(Transaction)
        )
        result = await session.execute(stmt)
        await session.commit()
        return result.scalar_one_or_none()

async def get_user_transactions(
    user_id: int
) -> List[Transaction]:
    async with async_session() as session:
        query = select(Transaction).where(Transaction.user_id == user_id)
        result = await session.execute(query)
        return list(result.scalars().all())

#endregion

#region Support methods
async def create_support_ticket(
    user_id: int,
    subject: str,
    message: str,
    status: str = "open"
) -> Support:
    async with async_session() as session:
        try:
            ticket = Support(
                user_id=user_id,
                subject=subject,
                message=message,
                status=status
            )
            session.add(ticket)
            await session.commit()
            await session.refresh(ticket)
            return ticket
        except Exception as e:
            print(f"Ошибка при создании тикета: {e}")
            raise e

async def get_user_support_tickets(
    user_id: int
) -> List[Support]:
    async with async_session() as session:
        query = select(Support).where(Support.user_id == user_id)
        result = await session.execute(query)
        return list(result.scalars().all())

async def update_support_ticket_status(
        ticket_id: int,
    status: str
) -> Optional[Support]:
    async with async_session() as session:
        stmt = (
            update(Support)
            .where(Support.id == ticket_id)
            .values(status=status)
            .returning(Support)
        )
    result = await session.execute(stmt)
    await session.commit()
    return result.scalar_one_or_none()

async def get_support_tickets_by_status(
    status: str
) -> List[Support]:
    async with async_session() as session:
        query = select(Support).where(Support.status == status)
        result = await session.execute(query)
        return list(result.scalars().all())
  
#endregion
