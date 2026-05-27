"""
ETL Service: Data loading, transformation, and pipeline utilities
"""

import os
import json
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import numpy as np
import cv2
from collections import defaultdict

from ..utils.helpers import ImageProcessor


class ETLService:
    """ETL (Extract, Transform, Load) service for waste classification data"""
    
    # Class mappings for both datasets
    REALWASTE_CLASSES = [
        'Cardboard', 'Food Organics', 'Glass', 'Metal', 
        'Miscellaneous Trash', 'Paper', 'Plastic', 'Textile Trash', 'Vegetation'
    ]
    
    TACO_CLASSES = [
        'Plastic bag', 'Plastic bottle', 'Plastic cup', 'Plastic other',
        'Paper', 'Cardboard', 'Metal', 'Glass', 'Textile', 'Organic',
        'Other trash'
    ]
    
    # Unified class mapping (filesystem-safe internal labels)
    UNIFIED_CLASSES = [
        'Plastic', 'Organic', 'Metal', 'Paper_Cardboard', 'Glass', 'Textile', 'Miscellaneous'
    ]
    
    @staticmethod
    def get_realwaste_mapping() -> Dict[str, str]:
        """Map RealWaste folder names to unified classes"""
        return {
            'Cardboard': 'Paper_Cardboard',
            'Food Organics': 'Organic',
            'Glass': 'Glass',
            'Metal': 'Metal',
            'Miscellaneous Trash': 'Miscellaneous',
            'Paper': 'Paper_Cardboard',
            'Plastic': 'Plastic',
            'Textile Trash': 'Textile',
            'Vegetation': 'Organic'
        }
    
    @staticmethod
    def get_taco_mapping() -> Dict[str, str]:
        """Map TACO labels to unified classes"""
        return {
            'Plastic bag': 'Plastic',
            'Plastic bottle': 'Plastic',
            'Plastic cup': 'Plastic',
            'Plastic other': 'Plastic',
            'Paper': 'Paper_Cardboard',
            'Cardboard': 'Paper_Cardboard',
            'Metal': 'Metal',
            'Glass': 'Glass',
            'Textile': 'Textile',
            'Organic': 'Organic',
            'Other trash': 'Miscellaneous'
        }
    
    @staticmethod
    def organize_realwaste(realwaste_path: str, output_path: str) -> Dict[str, int]:
        """
        Organize RealWaste dataset into unified class folders
        
        Args:
            realwaste_path: Path to extracted RealWaste folder
            output_path: Path to output organized data
        
        Returns:
            Statistics of organized data
        """
        output_dir = Path(output_path)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        mapping = ETLService.get_realwaste_mapping()
        stats = defaultdict(int)
        
        realwaste_dir = Path(realwaste_path) / 'RealWaste'
        
        if not realwaste_dir.exists():
            realwaste_dir = Path(realwaste_path)
        
        for folder_name, unified_class in mapping.items():
            source_folder = realwaste_dir / folder_name
            target_folder = output_dir / unified_class
            target_folder.mkdir(parents=True, exist_ok=True)
            
            if source_folder.exists():
                # Copy images
                for img_file in source_folder.glob('*.jpg'):
                    try:
                        dest_path = target_folder / img_file.name
                        shutil.copy(str(img_file), str(dest_path))
                        stats[unified_class] += 1
                    except Exception as e:
                        print(f"Error copying {img_file}: {e}")
                
                for img_file in source_folder.glob('*.png'):
                    try:
                        dest_path = target_folder / img_file.name
                        shutil.copy(str(img_file), str(dest_path))
                        stats[unified_class] += 1
                    except Exception as e:
                        print(f"Error copying {img_file}: {e}")
        
        return dict(stats)
    
    @staticmethod
    def organize_taco(taco_path: str, output_path: str) -> Dict[str, int]:
        """
        Organize TACO dataset using annotations
        
        Args:
            taco_path: Path to TACO dataset
            output_path: Path to output organized data
        
        Returns:
            Statistics of organized data
        """
        output_dir = Path(output_path)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        mapping = ETLService.get_taco_mapping()
        stats = defaultdict(int)
        
        taco_dir = Path(taco_path)
        annotations_file = taco_dir / 'data' / 'annotations.json'
        
        if not annotations_file.exists():
            print(f"⚠ Annotations file not found: {annotations_file}")
            return dict(stats)
        
        with open(annotations_file, 'r') as f:
            annotations = json.load(f)
        
        # Create category mapping
        category_id_to_name = {}
        for cat in annotations.get('categories', []):
            category_id_to_name[cat['id']] = cat['name']
        
        # Process images
        for image_info in annotations.get('images', []):
            image_id = image_info['id']
            image_path = taco_dir / 'data' / image_info['file_name']
            
            if not image_path.exists():
                continue
            
            # Find annotations for this image
            image_annotations = [a for a in annotations.get('annotations', []) 
                                if a['image_id'] == image_id]
            
            if not image_annotations:
                continue
            
            # Get primary class (first annotation)
            primary_annotation = image_annotations[0]
            category_id = primary_annotation['category_id']
            category_name = category_id_to_name.get(category_id, 'Other trash')
            
            # Map to unified class
            unified_class = mapping.get(category_name, 'Miscellaneous')
            target_folder = output_dir / unified_class
            target_folder.mkdir(parents=True, exist_ok=True)
            
            try:
                dest_path = target_folder / image_path.name
                shutil.copy(str(image_path), str(dest_path))
                stats[unified_class] += 1
            except Exception as e:
                print(f"Error copying {image_path}: {e}")
        
        return dict(stats)
    
    @staticmethod
    def canonical_class_name(folder_name: str) -> str:
        """Map dataset folder names to ImageProcessor.CLASS_NAMES labels."""
        aliases = {
            "Paper": "Paper_Cardboard",
            "Cardboard": "Paper_Cardboard",
            "Food Organics": "Organic",
            "Vegetation": "Organic",
            "Textile Trash": "Textile",
            "Miscellaneous Trash": "Miscellaneous",
        }
        return aliases.get(folder_name, folder_name)

    @staticmethod
    def split_dataset(source_path: str, output_path: str, 
                     train_ratio: float = 0.7, 
                     val_ratio: float = 0.15) -> Dict:
        """
        Split organized dataset into train/val/test
        
        Args:
            source_path: Path to organized class folders
            output_path: Output path for split data
            train_ratio: Fraction for training
            val_ratio: Fraction for validation
        
        Returns:
            Statistics of split
        """
        import random
        
        output_dir = Path(output_path)
        splits_dir = output_dir / 'splits'
        splits_dir.mkdir(parents=True, exist_ok=True)
        
        # Create split folders
        for split in ['train', 'val', 'test']:
            split_folder = splits_dir / split
            split_folder.mkdir(exist_ok=True)
        
        stats = {
            'train': defaultdict(int),
            'val': defaultdict(int),
            'test': defaultdict(int)
        }
        
        # Process each class
        for class_folder in Path(source_path).iterdir():
            if not class_folder.is_dir():
                continue
            
            class_name = ETLService.canonical_class_name(class_folder.name)
            if class_name not in ImageProcessor.CLASS_NAMES:
                continue
            images = list(class_folder.glob('*.jpg')) + list(class_folder.glob('*.png'))
            random.shuffle(images)
            
            total = len(images)
            train_idx = int(total * train_ratio)
            val_idx = int(total * (train_ratio + val_ratio))
            
            # Train split
            for img_path in images[:train_idx]:
                target = splits_dir / 'train' / class_name / img_path.name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(str(img_path), str(target))
                stats['train'][class_name] += 1
            
            # Validation split
            for img_path in images[train_idx:val_idx]:
                target = splits_dir / 'val' / class_name / img_path.name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(str(img_path), str(target))
                stats['val'][class_name] += 1
            
            # Test split
            for img_path in images[val_idx:]:
                target = splits_dir / 'test' / class_name / img_path.name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(str(img_path), str(target))
                stats['test'][class_name] += 1
        
        return {split: dict(counts) for split, counts in stats.items()}
    
    @staticmethod
    def get_dataset_stats(dataset_path: str) -> Dict:
        """Get statistics of organized dataset"""
        stats = defaultdict(int)
        total_size = 0
        
        for class_folder in Path(dataset_path).iterdir():
            if not class_folder.is_dir():
                continue
            
            for img_path in class_folder.glob('*'):
                if img_path.is_file():
                    stats[class_folder.name] += 1
                    total_size += img_path.stat().st_size
        
        return {
            'class_distribution': dict(stats),
            'total_images': sum(stats.values()),
            'total_size_mb': total_size / (1024 * 1024),
            'classes': list(stats.keys())
        }
