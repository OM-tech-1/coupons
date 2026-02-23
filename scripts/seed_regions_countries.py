"""
Seed script for populating regions and countries.

This script populates the database with common regions and countries
organized by geographical areas. It's idempotent - safe to run multiple times.

Usage:
    python scripts/seed_regions_countries.py
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models.region import Region
from app.models.country import Country
from sqlalchemy.exc import IntegrityError
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Region and Country data structure
REGIONS_DATA = [
    {
        "name": "Middle East",
        "slug": "middle-east",
        "is_active": True,
        "countries": [
            {"name": "United Arab Emirates", "slug": "united-arab-emirates", "code": "AE"},
            {"name": "Saudi Arabia", "slug": "saudi-arabia", "code": "SA"},
            {"name": "Qatar", "slug": "qatar", "code": "QA"},
            {"name": "Kuwait", "slug": "kuwait", "code": "KW"},
            {"name": "Bahrain", "slug": "bahrain", "code": "BH"},
            {"name": "Oman", "slug": "oman", "code": "OM"},
            {"name": "Jordan", "slug": "jordan", "code": "JO"},
            {"name": "Lebanon", "slug": "lebanon", "code": "LB"},
        ]
    },
    {
        "name": "South Asia",
        "slug": "south-asia",
        "is_active": True,
        "countries": [
            {"name": "India", "slug": "india", "code": "IN"},
            {"name": "Pakistan", "slug": "pakistan", "code": "PK"},
            {"name": "Bangladesh", "slug": "bangladesh", "code": "BD"},
            {"name": "Sri Lanka", "slug": "sri-lanka", "code": "LK"},
            {"name": "Nepal", "slug": "nepal", "code": "NP"},
            {"name": "Maldives", "slug": "maldives", "code": "MV"},
        ]
    },
    {
        "name": "Southeast Asia",
        "slug": "southeast-asia",
        "is_active": True,
        "countries": [
            {"name": "Singapore", "slug": "singapore", "code": "SG"},
            {"name": "Malaysia", "slug": "malaysia", "code": "MY"},
            {"name": "Indonesia", "slug": "indonesia", "code": "ID"},
            {"name": "Thailand", "slug": "thailand", "code": "TH"},
            {"name": "Philippines", "slug": "philippines", "code": "PH"},
            {"name": "Vietnam", "slug": "vietnam", "code": "VN"},
        ]
    },
    {
        "name": "East Asia",
        "slug": "east-asia",
        "is_active": True,
        "countries": [
            {"name": "China", "slug": "china", "code": "CN"},
            {"name": "Japan", "slug": "japan", "code": "JP"},
            {"name": "South Korea", "slug": "south-korea", "code": "KR"},
            {"name": "Hong Kong", "slug": "hong-kong", "code": "HK"},
            {"name": "Taiwan", "slug": "taiwan", "code": "TW"},
        ]
    },
    {
        "name": "North America",
        "slug": "north-america",
        "is_active": True,
        "countries": [
            {"name": "United States", "slug": "united-states", "code": "US"},
            {"name": "Canada", "slug": "canada", "code": "CA"},
            {"name": "Mexico", "slug": "mexico", "code": "MX"},
        ]
    },
    {
        "name": "Europe",
        "slug": "europe",
        "is_active": True,
        "countries": [
            {"name": "United Kingdom", "slug": "united-kingdom", "code": "GB"},
            {"name": "Germany", "slug": "germany", "code": "DE"},
            {"name": "France", "slug": "france", "code": "FR"},
            {"name": "Italy", "slug": "italy", "code": "IT"},
            {"name": "Spain", "slug": "spain", "code": "ES"},
            {"name": "Netherlands", "slug": "netherlands", "code": "NL"},
            {"name": "Switzerland", "slug": "switzerland", "code": "CH"},
            {"name": "Sweden", "slug": "sweden", "code": "SE"},
            {"name": "Norway", "slug": "norway", "code": "NO"},
            {"name": "Denmark", "slug": "denmark", "code": "DK"},
        ]
    },
    {
        "name": "Oceania",
        "slug": "oceania",
        "is_active": True,
        "countries": [
            {"name": "Australia", "slug": "australia", "code": "AU"},
            {"name": "New Zealand", "slug": "new-zealand", "code": "NZ"},
        ]
    },
    {
        "name": "Africa",
        "slug": "africa",
        "is_active": True,
        "countries": [
            {"name": "South Africa", "slug": "south-africa", "code": "ZA"},
            {"name": "Egypt", "slug": "egypt", "code": "EG"},
            {"name": "Nigeria", "slug": "nigeria", "code": "NG"},
            {"name": "Kenya", "slug": "kenya", "code": "KE"},
            {"name": "Morocco", "slug": "morocco", "code": "MA"},
        ]
    },
    {
        "name": "South America",
        "slug": "south-america",
        "is_active": True,
        "countries": [
            {"name": "Brazil", "slug": "brazil", "code": "BR"},
            {"name": "Argentina", "slug": "argentina", "code": "AR"},
            {"name": "Chile", "slug": "chile", "code": "CL"},
            {"name": "Colombia", "slug": "colombia", "code": "CO"},
            {"name": "Peru", "slug": "peru", "code": "PE"},
        ]
    },
]


def seed_regions_and_countries():
    """Seed regions and countries into the database"""
    db = SessionLocal()
    
    try:
        total_regions = 0
        total_countries = 0
        skipped_regions = 0
        skipped_countries = 0
        
        logger.info("Starting region and country seeding...")
        
        for region_data in REGIONS_DATA:
            # Check if region already exists
            existing_region = db.query(Region).filter(
                Region.slug == region_data["slug"]
            ).first()
            
            if existing_region:
                logger.info(f"Region '{region_data['name']}' already exists, skipping...")
                region = existing_region
                skipped_regions += 1
            else:
                # Create region
                region = Region(
                    name=region_data["name"],
                    slug=region_data["slug"],
                    is_active=region_data["is_active"]
                )
                db.add(region)
                db.flush()  # Get the region ID
                total_regions += 1
                logger.info(f"✓ Created region: {region_data['name']}")
            
            # Create countries for this region
            for country_data in region_data["countries"]:
                # Check if country already exists
                existing_country = db.query(Country).filter(
                    Country.country_code == country_data["code"]
                ).first()
                
                if existing_country:
                    logger.debug(f"  Country '{country_data['name']}' already exists, skipping...")
                    skipped_countries += 1
                    continue
                
                # Create country
                country = Country(
                    name=country_data["name"],
                    slug=country_data["slug"],
                    country_code=country_data["code"],
                    region_id=region.id,
                    is_active=True
                )
                db.add(country)
                total_countries += 1
                logger.info(f"  ✓ Created country: {country_data['name']} ({country_data['code']})")
        
        # Commit all changes
        db.commit()
        
        # Summary
        logger.info("\n" + "="*60)
        logger.info("SEEDING COMPLETE")
        logger.info("="*60)
        logger.info(f"Regions created: {total_regions}")
        logger.info(f"Regions skipped (already exist): {skipped_regions}")
        logger.info(f"Countries created: {total_countries}")
        logger.info(f"Countries skipped (already exist): {skipped_countries}")
        logger.info(f"Total regions in database: {total_regions + skipped_regions}")
        logger.info(f"Total countries in database: {total_countries + skipped_countries}")
        logger.info("="*60)
        
        return True
        
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Database integrity error: {e}")
        logger.error("This might be due to duplicate slugs or country codes.")
        return False
    except Exception as e:
        db.rollback()
        logger.error(f"Error seeding data: {e}")
        return False
    finally:
        db.close()


def verify_seeding():
    """Verify that regions and countries were seeded correctly"""
    db = SessionLocal()
    
    try:
        region_count = db.query(Region).count()
        country_count = db.query(Country).count()
        active_country_count = db.query(Country).filter(Country.is_active == True).count()
        
        logger.info("\nVERIFICATION:")
        logger.info(f"Total regions: {region_count}")
        logger.info(f"Total countries: {country_count}")
        logger.info(f"Active countries: {active_country_count}")
        
        # Show sample data
        logger.info("\nSample regions:")
        regions = db.query(Region).limit(3).all()
        for region in regions:
            country_count_in_region = db.query(Country).filter(
                Country.region_id == region.id
            ).count()
            logger.info(f"  - {region.name} ({country_count_in_region} countries)")
        
        return True
    except Exception as e:
        logger.error(f"Error verifying data: {e}")
        return False
    finally:
        db.close()


if __name__ == "__main__":
    logger.info("="*60)
    logger.info("REGION & COUNTRY SEEDING SCRIPT")
    logger.info("="*60)
    
    success = seed_regions_and_countries()
    
    if success:
        verify_seeding()
        logger.info("\n✅ Seeding completed successfully!")
        logger.info("\nYou can now access:")
        logger.info("  - GET /regions/ - List all regions")
        logger.info("  - GET /countries/ - List all countries")
        logger.info("  - GET /countries/?active_only=true - List active countries")
    else:
        logger.error("\n❌ Seeding failed. Please check the errors above.")
        sys.exit(1)
