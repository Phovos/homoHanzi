import pathlib
import json
import yaml
import re
import csv
import os
from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Union, Any
from enum import Enum

class RadicalType(Enum):
    SEMANTIC = "semantic"  # Provides meaning
    PHONETIC = "phonetic"  # Provides pronunciation
    BOTH = "both"          # Both semantic and phonetic
    UNKNOWN = "unknown"    # Not yet classified

class StrokeType(Enum):
    HORIZONTAL = "横"      # Horizontal stroke
    VERTICAL = "竖"        # Vertical stroke
    LEFT_DIAGONAL = "撇"   # Left-falling diagonal stroke
    RIGHT_DIAGONAL = "捺"  # Right-falling diagonal stroke
    DOT = "点"             # Dot stroke
    HOOK = "钩"            # Hook stroke
    RISING = "提"          # Rising stroke
    BEND = "折"            # Bent stroke

@dataclass
class Radical:
    """Representation of a Chinese radical"""
    character: str         # The radical character itself
    pinyin: str            # Pinyin pronunciation
    meaning: str           # English meaning
    type: RadicalType      # Type of radical (semantic/phonetic)
    strokes: int           # Number of strokes
    stroke_order: List[StrokeType] = field(default_factory=list)
    common_characters: List[str] = field(default_factory=list)
    mnemonic: str = ""     # Memory aid for this radical

@dataclass
class Character:
    """Representation of a Chinese character"""
    character: str         # The character itself
    pinyin: str            # Pinyin pronunciation
    tone: int              # Tone (1-5)
    meaning: List[str]     # List of English meanings
    radicals: List[str]    # List of component radicals
    strokes: int           # Total number of strokes
    stroke_order: List[StrokeType] = field(default_factory=list)
    components: List[str] = field(default_factory=list)  # Other characters that make up this character
    hsk_level: int = 0     # HSK level (0 if not in HSK)
    frequency_rank: int = 0  # Frequency rank in corpus (0 if unknown)
    mnemonic: str = ""     # Memory aid for this character
    example_words: List[Dict[str, str]] = field(default_factory=list)  # Example words containing this character
    tags: List[str] = field(default_factory=list)  # Custom tags

class ChineseCharacterSystem:
    """Manager for Chinese character learning system"""
    def __init__(self, root_dir: Union[str, pathlib.Path], vscode_dir: Union[str, pathlib.Path], 
                obsidian_dir: Union[str, pathlib.Path]):
        self.root_dir = pathlib.Path(root_dir)
        self.vscode_dir = pathlib.Path(vscode_dir)
        self.obsidian_dir = pathlib.Path(obsidian_dir)
        
        # Ensure directories exist
        self.root_dir.mkdir(parents=True, exist_ok=True)
        self.vscode_dir.mkdir(parents=True, exist_ok=True)
        self.obsidian_dir.mkdir(parents=True, exist_ok=True)
        
        # Data stores
        self.radicals: Dict[str, Radical] = {}
        self.characters: Dict[str, Character] = {}
        self.radical_index: Dict[str, Set[str]] = {}  # Radical -> Set of characters containing it
        
        # Load existing data
        self.load_data()
    
    def load_data(self):
        """Load existing character and radical data"""
        # Load radicals
        radical_dir = self.root_dir / "radicals"
        if radical_dir.exists():
            for file_path in radical_dir.glob("*.md"):
                radical = self._parse_radical_file(file_path)
                if radical:
                    self.radicals[radical.character] = radical
        
        # Load characters
        char_dir = self.root_dir / "characters"
        if char_dir.exists():
            for file_path in char_dir.glob("*.md"):
                character = self._parse_character_file(file_path)
                if character:
                    self.characters[character.character] = character
                    
                    # Update radical index
                    for radical in character.radicals:
                        if radical not in self.radical_index:
                            self.radical_index[radical] = set()
                        self.radical_index[radical].add(character.character)
    
    def _parse_radical_file(self, file_path: pathlib.Path) -> Optional[Radical]:
        """Parse a radical markdown file"""
        try:
            content = file_path.read_text(encoding="utf-8")
            
            # Extract YAML frontmatter
            yaml_match = re.search(r"^---\n(.*?)\n---", content, re.DOTALL)
            if yaml_match:
                frontmatter = yaml.safe_load(yaml_match.group(1))
                
                # Create Radical object
                radical = Radical(
                    character=frontmatter.get("character", ""),
                    pinyin=frontmatter.get("pinyin", ""),
                    meaning=frontmatter.get("meaning", ""),
                    type=RadicalType(frontmatter.get("type", "unknown")),
                    strokes=frontmatter.get("strokes", 0),
                    mnemonic=frontmatter.get("mnemonic", "")
                )
                
                # Parse stroke order if available
                stroke_order = frontmatter.get("stroke_order", [])
                if stroke_order:
                    radical.stroke_order = [StrokeType(s) for s in stroke_order]
                
                # Parse common characters if available
                common_chars = frontmatter.get("common_characters", [])
                if common_chars:
                    radical.common_characters = common_chars
                
                return radical
            
            return None
        except Exception as e:
            print(f"Error parsing radical file {file_path}: {e}")
            return None
    
    def _parse_character_file(self, file_path: pathlib.Path) -> Optional[Character]:
        """Parse a character markdown file"""
        try:
            content = file_path.read_text(encoding="utf-8")
            
            # Extract YAML frontmatter
            yaml_match = re.search(r"^---\n(.*?)\n---", content, re.DOTALL)
            if yaml_match:
                frontmatter = yaml.safe_load(yaml_match.group(1))
                
                # Create Character object
                character = Character(
                    character=frontmatter.get("character", ""),
                    pinyin=frontmatter.get("pinyin", ""),
                    tone=frontmatter.get("tone", 0),
                    meaning=frontmatter.get("meaning", []),
                    radicals=frontmatter.get("radicals", []),
                    strokes=frontmatter.get("strokes", 0),
                    hsk_level=frontmatter.get("hsk_level", 0),
                    frequency_rank=frontmatter.get("frequency_rank", 0),
                    mnemonic=frontmatter.get("mnemonic", "")
                )
                
                # Parse stroke order if available
                stroke_order = frontmatter.get("stroke_order", [])
                if stroke_order:
                    character.stroke_order = [StrokeType(s) for s in stroke_order]
                
                # Parse components if available
                components = frontmatter.get("components", [])
                if components:
                    character.components = components
                
                # Parse example words if available
                example_words = frontmatter.get("example_words", [])
                if example_words:
                    character.example_words = example_words
                
                # Parse tags if available
                tags = frontmatter.get("tags", [])
                if tags:
                    character.tags = tags
                
                return character
            
            return None
        except Exception as e:
            print(f"Error parsing character file {file_path}: {e}")
            return None
    
    def add_radical(self, radical: Radical) -> bool:
        """Add a new radical to the system"""
        if radical.character in self.radicals:
            print(f"Radical {radical.character} already exists")
            return False
        
        # Add to memory
        self.radicals[radical.character] = radical
        
        # Write to file
        self._save_radical(radical)
        return True
    
    def add_character(self, character: Character) -> bool:
        """Add a new character to the system"""
        if character.character in self.characters:
            print(f"Character {character.character} already exists")
            return False
        
        # Add to memory
        self.characters[character.character] = character
        
        # Update radical index
        for radical in character.radicals:
            if radical not in self.radical_index:
                self.radical_index[radical] = set()
            self.radical_index[radical].add(character.character)
        
        # Write to file
        self._save_character(character)
        return True
    
    def _save_radical(self, radical: Radical):
        """Save a radical to its markdown file"""
        radical_dir = self.root_dir / "radicals"
        radical_dir.mkdir(parents=True, exist_ok=True)
        
        # Create frontmatter
        frontmatter = {
            "character": radical.character,
            "pinyin": radical.pinyin,
            "meaning": radical.meaning,
            "type": radical.type.value,
            "strokes": radical.strokes,
            "mnemonic": radical.mnemonic
        }
        
        if radical.stroke_order:
            frontmatter["stroke_order"] = [stroke.value for stroke in radical.stroke_order]
        
        if radical.common_characters:
            frontmatter["common_characters"] = radical.common_characters
        
        # Prepare content
        content = f"""---
{yaml.dump(frontmatter, allow_unicode=True)}---

# {radical.character} - {radical.meaning}

## Overview
- **Pinyin**: {radical.pinyin}
- **Type**: {radical.type.value}
- **Strokes**: {radical.strokes}

## Mnemonic
{radical.mnemonic}

## Common Characters
{', '.join(radical.common_characters)}

## Stroke Order
{' → '.join([stroke.value for stroke in radical.stroke_order])}
"""
        
        # Write to file
        file_path = radical_dir / f"{radical.character}.md"
        file_path.write_text(content, encoding="utf-8")
        
        # Create VS Code version (could be the same or customized)
        vscode_radical_dir = self.vscode_dir / "radicals"
        vscode_radical_dir.mkdir(parents=True, exist_ok=True)
        vscode_file_path = vscode_radical_dir / f"{radical.character}.md"
        vscode_file_path.write_text(content, encoding="utf-8")
        
        # Create Obsidian version (with potential Obsidian-specific formatting)
        obsidian_radical_dir = self.obsidian_dir / "radicals"
        obsidian_radical_dir.mkdir(parents=True, exist_ok=True)
        
        # Add Obsidian-specific content (e.g., callouts, links to related notes)
        obsidian_content = f"""---
{yaml.dump(frontmatter, allow_unicode=True)}---

# {radical.character} - {radical.meaning}

## Overview
- **Pinyin**: {radical.pinyin}
- **Type**: {radical.type.value}
- **Strokes**: {radical.strokes}

## Mnemonic
> [!hint] Memory Aid
> {radical.mnemonic}

## Common Characters
{', '.join([f"[[{char}]]" for char in radical.common_characters])}

## Stroke Order
{' → '.join([stroke.value for stroke in radical.stroke_order])}

## Practice
![[{radical.character}_stroke_order.gif]]

> [!question] Flashcard
> What is the meaning of {radical.character}?
> 
> > [!success] Answer
> > {radical.meaning}
"""
        
        obsidian_file_path = obsidian_radical_dir / f"{radical.character}.md"
        obsidian_file_path.write_text(obsidian_content, encoding="utf-8")
    
    def _save_character(self, character: Character):
        """Save a character to its markdown file"""
        char_dir = self.root_dir / "characters"
        char_dir.mkdir(parents=True, exist_ok=True)
        
        # Create frontmatter
        frontmatter = {
            "character": character.character,
            "pinyin": character.pinyin,
            "tone": character.tone,
            "meaning": character.meaning,
            "radicals": character.radicals,
            "strokes": character.strokes,
            "mnemonic": character.mnemonic
        }
        
        if character.stroke_order:
            frontmatter["stroke_order"] = [stroke.value for stroke in character.stroke_order]
        
        if character.components:
            frontmatter["components"] = character.components
        
        if character.example_words:
            frontmatter["example_words"] = character.example_words
        
        if character.tags:
            frontmatter["tags"] = character.tags
        
        if character.hsk_level:
            frontmatter["hsk_level"] = character.hsk_level
        
        if character.frequency_rank:
            frontmatter["frequency_rank"] = character.frequency_rank
        
        # Prepare content
        content = f"""---
{yaml.dump(frontmatter, allow_unicode=True)}---

# {character.character} - {', '.join(character.meaning)}

## Overview
- **Pinyin**: {character.pinyin} (Tone {character.tone})
- **Radicals**: {', '.join(character.radicals)}
- **Components**: {', '.join(character.components)}
- **Strokes**: {character.strokes}
- **HSK Level**: {character.hsk_level or "N/A"}
- **Frequency Rank**: {character.frequency_rank or "N/A"}

## Mnemonic
{character.mnemonic}

## Example Words
"""
        
        for word in character.example_words:
            content += f"- {word['word']} ({word['pinyin']}): {word['meaning']}\n"
        
        content += """
## Stroke Order
"""
        content += ' → '.join([stroke.value for stroke in character.stroke_order])
        
        # Write to file
        file_path = char_dir / f"{character.character}.md"
        file_path.write_text(content, encoding="utf-8")
        
        # Create VS Code version (with code snippets and extended metadata)
        vscode_char_dir = self.vscode_dir / "characters"
        vscode_char_dir.mkdir(parents=True, exist_ok=True)
        
        vscode_content = content + f"""
## Code Snippet
```python
# Character metadata
char_data = {{
    "character": "{character.character}",
    "pinyin": "{character.pinyin}",
    "tone": {character.tone},
    "meaning": {json.dumps(character.meaning, ensure_ascii=False)},
    "radicals": {json.dumps(character.radicals, ensure_ascii=False)},
    "strokes": {character.strokes},
    "hsk_level": {character.hsk_level},
    "frequency_rank": {character.frequency_rank}
}}

# Export for Anki
anki_fields = f"{{character.character}}\\t{{character.pinyin}}\\t{{', '.join(character.meaning)}}\\t{{character.mnemonic}}"
```
"""
        
        vscode_file_path = vscode_char_dir / f"{character.character}.md"
        vscode_file_path.write_text(vscode_content, encoding="utf-8")
        
        # Create Obsidian version (with flashcards and internal links)
        obsidian_char_dir = self.obsidian_dir / "characters"
        obsidian_char_dir.mkdir(parents=True, exist_ok=True)
        
        obsidian_content = f"""---
{yaml.dump(frontmatter, allow_unicode=True)}---

# {character.character} - {', '.join(character.meaning)}

## Overview
- **Pinyin**: {character.pinyin} (Tone {character.tone})
- **Radicals**: {', '.join([f"[[radicals/{rad}|{rad}]]" for rad in character.radicals])}
- **Components**: {', '.join([f"[[{comp}]]" for comp in character.components])}
- **Strokes**: {character.strokes}
- **HSK Level**: {character.hsk_level or "N/A"}
- **Frequency Rank**: {character.frequency_rank or "N/A"}

## Mnemonic
> [!hint] Memory Aid
> {character.mnemonic}

## Example Words
"""
        
        for word in character.example_words:
            obsidian_content += f"- {word['word']} ({word['pinyin']}): {word['meaning']}\n"
        
        obsidian_content += """
## Stroke Order
"""
        obsidian_content += ' → '.join([stroke.value for stroke in character.stroke_order])
        
        obsidian_content += f"""

## Practice
![[{character.character}_stroke_order.gif]]

> [!question] Flashcard
> What is the meaning of {character.character}?
> 
> > [!success] Answer
> > {', '.join(character.meaning)}

> [!question] Flashcard
> How do you pronounce {character.character}?
> 
> > [!success] Answer
> > {character.pinyin} (Tone {character.tone})
"""
        
        obsidian_file_path = obsidian_char_dir / f"{character.character}.md"
        obsidian_file_path.write_text(obsidian_content, encoding="utf-8")
    
    def get_characters_by_radical(self, radical: str) -> List[Character]:
        """Get all characters containing a specific radical"""
        if radical not in self.radical_index:
            return []
        
        return [self.characters[char] for char in self.radical_index[radical] 
                if char in self.characters]
    
    def search_characters(self, query: str) -> List[Character]:
        """Search characters by pinyin, meaning, or tags"""
        results = []
        
        for char in self.characters.values():
            # Match by character
            if query in char.character:
                results.append(char)
                continue
            
            # Match by pinyin
            if query.lower() in char.pinyin.lower():
                results.append(char)
                continue
            
            # Match by meaning
            if any(query.lower() in meaning.lower() for meaning in char.meaning):
                results.append(char)
                continue
            
            # Match by tags
            if any(query.lower() in tag.lower() for tag in char.tags):
                results.append(char)
                continue
        
        return results

    def generate_anki_deck(self, output_path: pathlib.Path, include_radicals: bool = True) -> bool:
        """Generate an Anki-compatible TSV file for import"""
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, "w", encoding="utf-8") as f:
                # Write header
                f.write("character\tpinyin\tmeaning\tmnemonic\tradicals\tstrokes\n")
                
                # Write character data
                for char in self.characters.values():
                    f.write(f"{char.character}\t{char.pinyin}\t{', '.join(char.meaning)}\t{char.mnemonic}\t{', '.join(char.radicals)}\t{char.strokes}\n")
                
                # Optionally include radicals
                if include_radicals:
                    for radical in self.radicals.values():
                        f.write(f"{radical.character}\t{radical.pinyin}\t{radical.meaning}\t{radical.mnemonic}\t\t{radical.strokes}\n")
            
            return True
        except Exception as e:
            print(f"Error generating Anki deck: {e}")
            return False
    
    def generate_stroke_order_practice(self, output_dir: pathlib.Path) -> bool:
        """Generate stroke order practice sheets"""
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate HTML practice sheet
            html_content = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Chinese Character Practice Sheet</title>
    <style>
        body { font-family: Arial, sans-serif; }
        .grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; margin-bottom: 20px; }
        .cell { border: 1px solid #ccc; height: 100px; display: flex; justify-content: center; align-items: center; }
        .character { font-size: 24px; }
        .pinyin { font-size: 12px; color: #666; }
        .meaning { font-size: 10px; color: #999; }
        .practice-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; }
        .practice-cell { border: 1px solid #ccc; height: 100px; background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100"><line x1="0" y1="50" x2="100" y2="50" stroke="%23ddd" stroke-width="1"/><line x1="50" y1="0" x2="50" y2="100" stroke="%23ddd" stroke-width="1"/></svg>'); }
    </style>
</head>
<body>
    <h1>Chinese Character Practice Sheet</h1>
"""
            
            # Generate practice sheets for each character
            for char in list(self.characters.values())[:20]:  # Limit to 20 characters per sheet
                html_content += f"""
    <div class="character-section">
        <h2>{char.character} - {', '.join(char.meaning)}</h2>
        <p>Pinyin: {char.pinyin} (Tone {char.tone})</p>
        <p>Strokes: {char.strokes}</p>
        <p>Stroke Order: {' → '.join([stroke.value for stroke in char.stroke_order])}</p>
        
        <div class="grid">
            <div class="cell">
                <div class="character">{char.character}</div>
                <div class="pinyin">{char.pinyin}</div>
                <div class="meaning">{', '.join(char.meaning)}</div>
            </div>
        </div>
        
        <h3>Practice Grid</h3>
        <div class="practice-grid">
            <div class="practice-cell"></div>
            <div class="practice-cell"></div>
            <div class="practice-cell"></div>
            <div class="practice-cell"></div>
            <div class="practice-cell"></div>
            <div class="practice-cell"></div>
            <div class="practice-cell"></div>
            <div class="practice-cell"></div>
            <div class="practice-cell"></div>
            <div class="practice-cell"></div>
        </div>
    </div>
    <hr>
"""
            
            html_content += """
</body>
</html>
"""
            
            # Write HTML file
            html_path = output_dir / "practice_sheet.html"
            html_path.write_text(html_content, encoding="utf-8")
            
            # Generate PDF version (would require additional libraries in a real implementation)
            # Here we just note that it would be generated
            pdf_path = output_dir / "practice_sheet.pdf"
            with open(pdf_path, "w", encoding="utf-8") as f:
                f.write("This would be a PDF version of the practice sheet.")
            
            return True
        except Exception as e:
            print(f"Error generating practice sheets: {e}")
            return False
    
    def generate_stats(self) -> Dict[str, Any]:
        """Generate statistics about the learning progress"""
        stats = {
            "total_characters": len(self.characters),
            "total_radicals": len(self.radicals),
            "characters_by_hsk_level": {},
            "characters_by_stroke_count": {},
            "most_common_radicals": []
        }
        
        # Characters by HSK level
        for char in self.characters.values():
            hsk_level = char.hsk_level or 0
            if hsk_level not in stats["characters_by_hsk_level"]:
                stats["characters_by_hsk_level"][hsk_level] = 0
            stats["characters_by_hsk_level"][hsk_level] += 1
        
        # Characters by stroke count
        for char in self.characters.values():
            stroke_count = char.strokes
            if stroke_count not in stats["characters_by_stroke_count"]:
                stats["characters_by_stroke_count"][stroke_count] = 0
            stats["characters_by_stroke_count"][stroke_count] += 1
        
        # Most common radicals
        radical_count = {}
        for radical, chars in self.radical_index.items():
            radical_count[radical] = len(chars)
        
        stats["most_common_radicals"] = sorted(
            [{"radical": rad, "count": count} for rad, count in radical_count.items()],
            key=lambda x: x["count"],
            reverse=True
        )[:10]  # Top 10
        
        return stats
    
    def import_from_csv(self, csv_path: pathlib.Path) -> int:
        """Import characters and radicals from a CSV file"""
        try:
            import csv
            
            count = 0
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    # Determine if this is a character or radical
                    is_radical = row.get("is_radical", "").lower() == "true"
                    
                    if is_radical:
                        # Create radical
                        radical = Radical(
                            character=row.get("character", ""),
                            pinyin=row.get("pinyin", ""),
                            meaning=row.get("meaning", ""),
                            type=RadicalType(row.get("type", "unknown")),
                            strokes=int(row.get("strokes", 0)),
                            mnemonic=row.get("mnemonic", "")
                        )
                        
                        # Parse stroke order if available
                        stroke_order = row.get("stroke_order", "")
                        if stroke_order:
                            radical.stroke_order = [StrokeType(s.strip()) for s in stroke_order.split(",")]
                        
                        # Parse common characters if available
                        common_chars = row.get("common_characters", "")
                        if common_chars:
                            radical.common_characters = [c.strip() for c in common_chars.split(",")]
                        
                        self.add_radical(radical)
                    else:
                        # Create character
                        meaning_list = [m.strip() for m in row.get("meaning", "").split(",")]
                        radicals_list = [r.strip() for r in row.get("radicals", "").split(",")]
                        
                        character = Character(
                            character=row.get("character", ""),
                            pinyin=row.get("pinyin", ""),
                            tone=int(row.get("tone", 0)),
                            meaning=meaning_list,
                            radicals=radicals_list,
                            strokes=int(row.get("strokes", 0)),
                            mnemonic=row.get("mnemonic", "")
                        )
                        
                        # Parse stroke order if available
                        stroke_order = row.get("stroke_order", "")
                        if stroke_order:
                            character.stroke_order = [StrokeType(s.strip()) for s in stroke_order.split(",")]
                        
                        # Parse components if available
                        components = row.get("components", "")
                        if components:
                            character.components = [c.strip() for c in components.split(",")]
                        
                        # Parse HSK level if available
                        hsk_level = row.get("hsk_level", "")
                        if hsk_level and hsk_level.isdigit():
                            character.hsk_level = int(hsk_level)
                        
                        # Parse frequency rank if available
                        freq_rank = row.get("frequency_rank", "")
                        if freq_rank and freq_rank.isdigit():
                            character.frequency_rank = int(freq_rank)
                        
                        # Parse tags if available
                        tags = row.get("tags", "")
                        if tags:
                            character.tags = [t.strip() for t in tags.split(",")]
                        
                        self.add_character(character)
                    
                    count += 1
            
            return count
        except Exception as e:
            print(f"Error importing from CSV: {e}")
            return 0
    
import argparse
import json
from pathlib import Path

def save_json_data(data, output_path):
    """Save list of row dictionaries to a JSON file"""
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(data)} rows to {output}")
def init_db(db_path: str):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pinyin (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_key TEXT,
        vowel_root TEXT,
        initial TEXT,
        final TEXT,
        actor TEXT
    )
    """)
    conn.commit()
    return conn

def load_pinyin_chart(csv_path: str):
    """
    Load the pinyin chart CSV without external libraries.
    Handles missing values and maps columns correctly.
    """
    pinyin_data = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader)  # First row is header

        for row_num, row in enumerate(reader):
            if not row:
                continue  # Skip empty lines

            row_data = {}
            for col_num, value in enumerate(row):
                col_name = headers[col_num] if col_num < len(headers) else f"col_{col_num}"
                row_data[col_name] = value.strip() if value.strip() else None

            pinyin_data.append(row_data)

    return pinyin_data

def insert_pinyin_row(conn, row_data):
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO pinyin (group_key, vowel_root, initial, final, actor)
    VALUES (?, ?, ?, ?, ?)
    """, (
        row_data.get("memory_palace_groups"),
        row_data.get("∅"),
        row_data.get("b"),
        row_data.get("p"),
        row_data.get("AEOIU")  # Assuming this column exists
    ))
    conn.commit()

def main():
    parser = argparse.ArgumentParser(description="Chinese Learning App CLI")
    parser.add_argument("--import-csv", help="Path to CSV file to import")
    parser.add_argument("--json-path", default="data/output.json", help="JSON output path")

    args = parser.parse_args()

    if args.import_csv:
        print(f"Loading CSV from {args.import_csv}...")
        data = load_pinyin_chart(args.import_csv)
        print(f"Loaded {len(data)} rows.")

        print("Saving to JSON...")
        save_json_data(data, args.json_path)


if __name__ == "__main__":
    main()