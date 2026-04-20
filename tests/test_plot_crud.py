"""
Comprehensive CRUD tests for the Plot model.

Tests cover:
- Create plot with valid/invalid data
- Read plot by id and user_id
- Update plot fields
- Delete plot
- List all plots for a user
"""
import pytest
import pytest_asyncio
from datetime import date
from typing import AsyncGenerator, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from src.hageglede.database import get_db
from src.models.plot import Plot
from src.schemas.plot import PlotCreate, PlotUpdate


# Test database setup
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    poolclass=NullPool,
)

AsyncTestingSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for each test."""
    async with engine.begin() as conn:
        # Create all tables
        from src.models.plot import Base
        await conn.run_sync(Base.metadata.create_all)
    
    async with AsyncTestingSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
    
    async with engine.begin() as conn:
        # Drop all tables
        from src.models.plot import Base
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def test_user_id() -> str:
    """Return a test user ID for tests."""
    return "test-user-123"


@pytest_asyncio.fixture(scope="function")
async def sample_plot_data(test_user_id: str) -> Dict[str, Any]:
    """Return sample valid plot data."""
    return {
        "user_id": test_user_id,
        "name": "My Vegetable Garden",
        "description": "A small garden with vegetables and herbs",
        "location": "Backyard",
        "size_square_meters": 25.5,
        "soil_type": "loamy",
        "sun_exposure": "full_sun",
        "watering_schedule": "daily",
        "notes": "Needs more compost",
        "created_date": date.today(),
        "last_updated": date.today()
    }


@pytest_asyncio.fixture(scope="function")
async def created_plot(db_session: AsyncSession, sample_plot_data: Dict[str, Any]) -> Plot:
    """Create and return a plot for testing read/update/delete operations."""
    plot = Plot(**sample_plot_data)
    db_session.add(plot)
    await db_session.commit()
    await db_session.refresh(plot)
    return plot


class TestCreatePlot:
    """Test creating plots with valid and invalid data."""
    
    async def test_create_plot_valid_data(self, db_session: AsyncSession, sample_plot_data: Dict[str, Any]):
        """Test creating a plot with valid data."""
        plot_create = PlotCreate(**sample_plot_data)
        plot = Plot(**plot_create.model_dump())
        
        db_session.add(plot)
        await db_session.commit()
        await db_session.refresh(plot)
        
        assert plot.id is not None
        assert plot.user_id == sample_plot_data["user_id"]
        assert plot.name == sample_plot_data["name"]
        assert plot.size_square_meters == sample_plot_data["size_square_meters"]
        assert plot.created_date == sample_plot_data["created_date"]
    
    async def test_create_plot_minimal_data(self, db_session: AsyncSession, test_user_id: str):
        """Test creating a plot with only required fields."""
        minimal_data = {
            "user_id": test_user_id,
            "name": "Minimal Plot",
            "created_date": date.today()
        }
        
        plot_create = PlotCreate(**minimal_data)
        plot = Plot(**plot_create.model_dump())
        
        db_session.add(plot)
        await db_session.commit()
        await db_session.refresh(plot)
        
        assert plot.id is not None
        assert plot.user_id == test_user_id
        assert plot.name == "Minimal Plot"
        assert plot.description is None
        assert plot.size_square_meters is None
    
    async def test_create_plot_invalid_size_negative(self, db_session: AsyncSession, test_user_id: str):
        """Test creating a plot with negative size should fail validation."""
        invalid_data = {
            "user_id": test_user_id,
            "name": "Invalid Plot",
            "size_square_meters": -10.0,
            "created_date": date.today()
        }
        
        # This should raise a validation error
        with pytest.raises(ValueError):
            plot_create = PlotCreate(**invalid_data)
    
    async def test_create_plot_missing_required_fields(self, test_user_id: str):
        """Test that missing required fields raises validation error."""
        incomplete_data = {
            "user_id": test_user_id,
            # Missing name - should fail
        }
        
        with pytest.raises(ValueError):
            plot_create = PlotCreate(**incomplete_data)


class TestReadPlot:
    """Test reading plots by various criteria."""
    
    async def test_read_plot_by_id(self, db_session: AsyncSession, created_plot: Plot):
        """Test reading a plot by its ID."""
        # Query the plot by ID
        result = await db_session.get(Plot, created_plot.id)
        
        assert result is not None
        assert result.id == created_plot.id
        assert result.user_id == created_plot.user_id
        assert result.name == created_plot.name
    
    async def test_read_plot_by_id_not_found(self, db_session: AsyncSession):
        """Test reading a non-existent plot returns None."""
        result = await db_session.get(Plot, 99999)  # Non-existent ID
        
        assert result is None
    
    async def test_read_plot_by_user_id(self, db_session: AsyncSession, created_plot: Plot, test_user_id: str):
        """Test reading plots by user ID."""
        from sqlalchemy import select
        
        # Query plots for the user
        stmt = select(Plot).where(Plot.user_id == test_user_id)
        result = await db_session.execute(stmt)
        plots = result.scalars().all()
        
        assert len(plots) == 1
        assert plots[0].id == created_plot.id
        assert plots[0].user_id == test_user_id
    
    async def test_read_plot_by_user_id_different_user(self, db_session: AsyncSession, created_plot: Plot):
        """Test that plots for different users are not returned."""
        from sqlalchemy import select
        
        # Query plots for a different user
        stmt = select(Plot).where(Plot.user_id == "different-user-456")
        result = await db_session.execute(stmt)
        plots = result.scalars().all()
        
        assert len(plots) == 0


class TestUpdatePlot:
    """Test updating plot fields."""
    
    async def test_update_plot_name(self, db_session: AsyncSession, created_plot: Plot):
        """Test updating the plot name."""
        original_name = created_plot.name
        
        # Update the name
        created_plot.name = "Updated Garden Name"
        await db_session.commit()
        await db_session.refresh(created_plot)
        
        assert created_plot.name == "Updated Garden Name"
        assert created_plot.name != original_name
        assert created_plot.last_updated == date.today()
    
    async def test_update_plot_description(self, db_session: AsyncSession, created_plot: Plot):
        """Test updating the plot description."""
        # Update description
        created_plot.description = "Updated description with more details"
        await db_session.commit()
        await db_session.refresh(created_plot)
        
        assert created_plot.description == "Updated description with more details"
        assert created_plot.last_updated == date.today()
    
    async def test_update_plot_multiple_fields(self, db_session: AsyncSession, created_plot: Plot):
        """Test updating multiple fields at once."""
        # Update multiple fields
        created_plot.name = "Completely New Name"
        created_plot.description = "New detailed description"
        created_plot.size_square_meters = 30.0
        created_plot.soil_type = "sandy"
        
        await db_session.commit()
        await db_session.refresh(created_plot)
        
        assert created_plot.name == "Completely New Name"
        assert created_plot.description == "New detailed description"
        assert created_plot.size_square_meters == 30.0
        assert created_plot.soil_type == "sandy"
        assert created_plot.last_updated == date.today()
    
    async def test_update_plot_with_schema(self, db_session: AsyncSession, created_plot: Plot):
        """Test updating using PlotUpdate schema."""
        update_data = {
            "name": "Schema Updated Name",
            "description": "Updated via schema",
            "sun_exposure": "partial_shade"
        }
        
        plot_update = PlotUpdate(**update_data)
        
        # Apply updates
        for field, value in plot_update.model_dump(exclude_unset=True).items():
            setattr(created_plot, field, value)
        
        await db_session.commit()
        await db_session.refresh(created_plot)
        
        assert created_plot.name == "Schema Updated Name"
        assert created_plot.description == "Updated via schema"
        assert created_plot.sun_exposure == "partial_shade"


class TestDeletePlot:
    """Test deleting plots."""
    
    async def test_delete_plot(self, db_session: AsyncSession, created_plot: Plot):
        """Test deleting a plot."""
        plot_id = created_plot.id
        
        # Delete the plot
        await db_session.delete(created_plot)
        await db_session.commit()
        
        # Verify it's gone
        result = await db_session.get(Plot, plot_id)
        assert result is None
    
    async def test_delete_plot_and_recreate(self, db_session: AsyncSession, sample_plot_data: Dict[str, Any]):
        """Test deleting a plot and creating a new one with same user."""
        # Create first plot
        plot1 = Plot(**sample_plot_data)
        db_session.add(plot1)
        await db_session.commit()
        await db_session.refresh(plot1)
        
        plot1_id = plot1.id
        
        # Delete it
        await db_session.delete(plot1)
        await db_session.commit()
        
        # Create new plot with same user
        sample_plot_data["name"] = "Recreated Plot"
        plot2 = Plot(**sample_plot_data)
        db_session.add(plot2)
        await db_session.commit()
        await db_session.refresh(plot2)
        
        # Verify new plot exists and old one doesn't
        result1 = await db_session.get(Plot, plot1_id)
        result2 = await db_session.get(Plot, plot2.id)
        
        assert result1 is None
        assert result2 is not None
        assert result2.name == "Recreated Plot"


class TestListPlots:
    """Test listing plots for a user."""
    
    async def test_list_all_plots_for_user(self, db_session: AsyncSession, test_user_id: str):
        """Test listing all plots for a specific user."""
        from sqlalchemy import select
        
        # Create multiple plots for the test user
        plots_data = [
            {
                "user_id": test_user_id,
                "name": f"Garden {i}",
                "description": f"Test garden {i}",
                "size_square_meters": 10.0 * (i + 1),
                "created_date": date.today()
            }
            for i in range(3)
        ]
        
        for plot_data in plots_data:
            plot = Plot(**plot_data)
            db_session.add(plot)
        
        await db_session.commit()
        
        # List all plots for the user
        stmt = select(Plot).where(Plot.user_id == test_user_id).order_by(Plot.name)
        result = await db_session.execute(stmt)
        plots = result.scalars().all()
        
        assert len(plots) == 3
        assert plots[0].name == "Garden 0"
        assert plots[1].name == "Garden 1"
        assert plots[2].name == "Garden 2"
    
    async def test_list_plots_empty_for_user(self, db_session: AsyncSession):
        """Test listing plots for a user with no plots returns empty list."""
        from sqlalchemy import select
        
        stmt = select(Plot).where(Plot.user_id == "user-with-no-plots")
        result = await db_session.execute(stmt)
        plots = result.scalars().all()
        
        assert len(plots) == 0
    
    async def test_list_plots_with_filtering(self, db_session: AsyncSession, test_user_id: str):
        """Test listing plots with additional filtering."""
        from sqlalchemy import select
        
        # Create plots with different sizes
        plots_data = [
            {"user_id": test_user_id, "name": "Small", "size_square_meters": 5.0, "created_date": date.today()},
            {"user_id": test_user_id, "name": "Medium", "size_square_meters": 15.0, "created_date": date.today()},
            {"user_id": test_user_id, "name": "Large", "size_square_meters": 25.0, "created_date": date.today()},
        ]
        
        for plot_data in plots_data:
            plot = Plot(**plot_data)
            db_session.add(plot)
        
        await db_session.commit()
        
        # List only medium and large plots (size > 10)
        stmt = select(Plot).where(
            Plot.user_id == test_user_id,
            Plot.size_square_meters > 10.0
        ).order_by(Plot.size_square_meters)
        
        result = await db_session.execute(stmt)
        plots = result.scalars().all()
        
        assert len(plots) == 2
        assert plots[0].name == "Medium"
        assert plots[1].name == "Large"
    
    async def test_list_plots_pagination(self, db_session: AsyncSession, test_user_id: str):
        """Test listing plots with pagination."""
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        
        # Create many plots
        for i in range(10):
            plot = Plot(
                user_id=test_user_id,
                name=f"Plot {i:02d}",
                created_date=date.today()
            )
            db_session.add(plot)
        
        await db_session.commit()
        
        # Get first page (5 plots)
        stmt = (
            select(Plot)
            .where(Plot.user_id == test_user_id)
            .order_by(Plot.name)
            .limit(5)
            .offset(0)
        )
        
        result = await db_session.execute(stmt)
        page1 = result.scalars().all()
        
        # Get second page (next 5 plots)
        stmt = (
            select(Plot)
            .where(Plot.user_id == test_user_id)
            .order_by(Plot.name)
            .limit(5)
            .offset(5)
        )
        
        result = await db_session.execute(stmt)
        page2 = result.scalars().all()
        
        assert len(page1) == 5
        assert len(page2) == 5
        assert page1[0].name == "Plot 00"
        assert page2[0].name == "Plot 05"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])