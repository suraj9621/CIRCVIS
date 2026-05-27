#!/usr/bin/env python3
"""
CIRCVIS ETL Pipeline
Organize, merge, and prepare RealWaste + TACO datasets
"""

import os
import sys
import argparse
import logging
from pathlib import Path
import zipfile

# Add project root to path so `backend` package is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.app.services.etl_service import ETLService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def extract_zip(zip_path: str, extract_to: str) -> str:
    """Extract zip file"""
    logger.info(f"Extracting {zip_path}...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
    logger.info(f"✓ Extracted to {extract_to}")
    return extract_to


def main():
    parser = argparse.ArgumentParser(
        description="CIRCVIS ETL Pipeline"
    )
    parser.add_argument(
        '--realwaste',
        help='Path to RealWaste zip or folder',
        default='data/raw/RealWaste'
    )
    parser.add_argument(
        '--taco',
        help='Path to TACO zip or folder',
        default='data/raw/TACO-master'
    )
    parser.add_argument(
        '--output',
        help='Output directory for organized data',
        default='data/processed'
    )
    parser.add_argument(
        '--skip-realwaste',
        action='store_true',
        help='Skip RealWaste processing'
    )
    parser.add_argument(
        '--skip-taco',
        action='store_true',
        help='Skip TACO processing'
    )
    
    args = parser.parse_args()
    
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    raw_dir = Path('data/raw')
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    organized_dir = output_dir / 'organized'
    organized_dir.mkdir(exist_ok=True)
    
    # Process RealWaste
    if not args.skip_realwaste:
        realwaste_path = Path(args.realwaste)
        
        if realwaste_path.suffix == '.zip':
            if not realwaste_path.exists():
                logger.warning(f"⚠ RealWaste zip not found at {realwaste_path}")
                logger.info("Please download from: https://github.com/real-waste/realwaste.github.io")
            else:
                extract_dir = raw_dir / 'realwaste'
                extract_zip(str(realwaste_path), str(extract_dir))
                realwaste_path = extract_dir
        
        if Path(realwaste_path).exists():
            logger.info("Processing RealWaste dataset...")
            stats = ETLService.organize_realwaste(str(realwaste_path), str(organized_dir))
            logger.info(f"✓ RealWaste organized: {stats}")
        else:
            logger.warning(f"⚠ RealWaste path not found: {realwaste_path}")
    
    # Process TACO
    if not args.skip_taco:
        taco_path = Path(args.taco)
        
        if taco_path.suffix == '.zip':
            if not taco_path.exists():
                logger.warning(f"⚠ TACO zip not found at {taco_path}")
                logger.info("Please download from: https://github.com/pedropro/TACO")
            else:
                extract_dir = raw_dir / 'taco'
                extract_zip(str(taco_path), str(extract_dir))
                taco_path = extract_dir / 'TACO-master'
        
        if Path(taco_path).exists():
            logger.info("Processing TACO dataset...")
            stats = ETLService.organize_taco(str(taco_path), str(organized_dir))
            logger.info(f"✓ TACO organized: {stats}")
        else:
            logger.warning(f"⚠ TACO path not found: {taco_path}")
    
    # Get dataset statistics
    logger.info("\n" + "="*60)
    logger.info("Dataset Statistics")
    logger.info("="*60)
    stats = ETLService.get_dataset_stats(str(organized_dir))
    logger.info(f"Total images: {stats['total_images']}")
    logger.info(f"Total size: {stats['total_size_mb']:.2f} MB")
    logger.info("\nClass distribution:")
    for class_name, count in sorted(stats['class_distribution'].items()):
        percentage = (count / stats['total_images']) * 100
        logger.info(f"  {class_name}: {count} images ({percentage:.1f}%)")
    
    # Split dataset
    logger.info("\n" + "="*60)
    logger.info("Splitting dataset into train/val/test")
    logger.info("="*60)
    split_stats = ETLService.split_dataset(str(organized_dir), str(output_dir))
    
    for split, counts in split_stats.items():
        total = sum(counts.values())
        logger.info(f"\n{split.upper()} ({total} images):")
        for class_name, count in sorted(counts.items()):
            percentage = (count / total) * 100
            logger.info(f"  {class_name}: {count} ({percentage:.1f}%)")
    
    logger.info("\n" + "="*60)
    logger.info("✓ ETL Pipeline Complete!")
    logger.info(f"Data ready at: {output_dir}")
    logger.info("="*60)


if __name__ == '__main__':
    main()
