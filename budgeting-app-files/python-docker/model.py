from sqlalchemy import DateTime, ForeignKey, Numeric, String, Integer
from datetime import datetime
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class Account(Base):
    __tablename__ = 'accounts'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String)
    email: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    transactions: Mapped[list["Transaction"]] = relationship(back_populates="account")

    def __repr__(self):
        return f"<Account(name='{self.name}', email='{self.email}', created_at='{self.created_at}')>"

class Transaction(Base):
    __tablename__ = 'transactions'

    id: Mapped[str] = mapped_column(String, primary_key=True)
    account_id: Mapped[str] = mapped_column(ForeignKey('accounts.id'))
    description: Mapped[str] = mapped_column(String)
    amount: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    entry_type: Mapped[str] = mapped_column(String)

    account: Mapped["Account"] = relationship(back_populates="transactions")

    def __repr__(self):
        return f"<Transaction(account_id='{self.account_id}', description='{self.description}', amount='{self.amount}', created_at='{self.created_at}', entry_type='{self.entry_type}')>"