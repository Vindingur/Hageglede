"""SQLAlchemy ORM models for Hageglede."""

import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Plant(Base):
    """Plant species or variety."""

    __tablename__ = "plants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    species: Mapped[Optional[str]] = mapped_column(String(100))
    variety: Mapped[Optional[str]] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text)
    days_to_maturity: Mapped[Optional[int]] = mapped_column(Integer)
    spacing_cm: Mapped[Optional[int]] = mapped_column(Integer)
    row_spacing_cm: Mapped[Optional[int]] = mapped_column(Integer)
    is_perennial: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )

    schedules: Mapped[list["PlantingSchedule"]] = relationship(
        back_populates="plant", cascade="all, delete-orphan"
    )
    pests: Mapped[list["Pest"]] = relationship(
        secondary="plant_pests", back_populates="plants"
    )

    def __repr__(self) -> str:
        return f"<Plant(id={self.id}, name='{self.name}')>"


class Zone(Base):
    """Garden zone/area with specific characteristics."""

    __tablename__ = "zones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    area_sqm: Mapped[Optional[float]] = mapped_column(Float)
    sunlight_hours: Mapped[Optional[int]] = mapped_column(Integer)
    soil_type: Mapped[Optional[str]] = mapped_column(String(50))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )

    schedules: Mapped[list["PlantingSchedule"]] = relationship(
        back_populates="zone", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Zone(id={self.id}, name='{self.name}')>"


class PlantingSchedule(Base):
    """Schedule for planting a specific plant in a zone."""

    __tablename__ = "planting_schedules"
    __table_args__ = (
        UniqueConstraint("plant_id", "zone_id", "year", name="uix_plant_zone_year"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plant_id: Mapped[int] = mapped_column(ForeignKey("plants.id", ondelete="CASCADE"))
    zone_id: Mapped[int] = mapped_column(ForeignKey("zones.id", ondelete="CASCADE"))
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    planned_date: Mapped[Optional[datetime.date]] = mapped_column(Date)
    actual_date: Mapped[Optional[datetime.date]] = mapped_column(Date)
    quantity: Mapped[Optional[int]] = mapped_column(Integer)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )

    plant: Mapped["Plant"] = relationship(back_populates="schedules")
    zone: Mapped["Zone"] = relationship(back_populates="schedules")

    def __repr__(self) -> str:
        return f"<PlantingSchedule(id={self.id}, plant_id={self.plant_id}, zone_id={self.zone_id}, year={self.year})>"


class Pest(Base):
    """Pest that affects plants."""

    __tablename__ = "pests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    scientific_name: Mapped[Optional[str]] = mapped_column(String(100))
    organic_control: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )

    plants: Mapped[list["Plant"]] = relationship(
        secondary="plant_pests", back_populates="pests"
    )

    def __repr__(self) -> str:
        return f"<Pest(id={self.id}, name='{self.name}')>"


# Association table for many-to-many relationship between plants and pests
class PlantPest(Base):
    """Association table linking plants to pests."""

    __tablename__ = "plant_pests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plant_id: Mapped[int] = mapped_column(
        ForeignKey("plants.id", ondelete="CASCADE"), nullable=False
    )
    pest_id: Mapped[int] = mapped_column(
        ForeignKey("pests.id", ondelete="CASCADE"), nullable=False
    )
    severity: Mapped[Optional[str]] = mapped_column(String(20))  # low, medium, high
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)

    __table_args__ = (UniqueConstraint("plant_id", "pest_id", name="uix_plant_pest"),)

    def __repr__(self) -> str:
        return f"<PlantPest(plant_id={self.plant_id}, pest_id={self.pest_id})>"