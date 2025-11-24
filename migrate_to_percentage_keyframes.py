"""
Migration script to convert wavemaker preset keyframes from absolute seconds to percentages.

This script converts all existing preset flow curves from time-in-seconds to time-as-percentage,
making curves independent of cycle duration.

Run this once: python migrate_to_percentage_keyframes.py
"""

import os
from app.services.storage import Store, make_db, WavemakerPreset
from sqlmodel import Session, select

def migrate_presets():
    db_url = os.getenv("DB_URL", "sqlite:///reef_controller.db")
    engine = make_db(db_url)
    store = Store(engine)
    
    with Session(store.engine) as session:
        statement = select(WavemakerPreset)
        presets = session.exec(statement).all()
        
        print(f"Found {len(presets)} presets to migrate")
        
        for preset in presets:
            cycle_duration = preset.cycle_duration_sec
            if cycle_duration <= 0:
                print(f"  Skipping preset '{preset.name}' (invalid cycle duration: {cycle_duration})")
                continue
            
            modified = False
            flow_curves = preset.flow_curves or {}
            
            for wm_key, curve in flow_curves.items():
                if not curve or len(curve) == 0:
                    continue
                
                for point in curve:
                    if 'time' in point:
                        time_sec = point['time']
                        time_pct = (time_sec / cycle_duration) * 100.0
                        point['time'] = round(time_pct, 2)
                        modified = True
            
            if modified:
                preset.flow_curves = flow_curves
                session.add(preset)
                print(f"  ✓ Migrated preset '{preset.name}' (cycle: {cycle_duration}s)")
        
        session.commit()
        print(f"\n✓ Migration complete!")

if __name__ == "__main__":
    migrate_presets()
