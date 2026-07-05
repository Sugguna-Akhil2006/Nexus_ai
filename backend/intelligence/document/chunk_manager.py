"""Handles document chunking strategies (semantic, markdown, CSV, JSON)."""

import json
import csv
import io
from typing import List, Dict, Any


class TextChunk:
    """A single segment of text with citation metadata details."""
    def __init__(self, chunk_id: str, text: str, section: str, start_char: int, end_char: int) -> None:
        self.chunk_id = chunk_id
        self.text = text
        self.section = section
        self.start_char = start_char
        self.end_char = end_char


class ChunkManager:
    """Manages document chunking strategies for diverse file types."""

    def chunk_document(
        self,
        content: str,
        file_format: str,
        chunk_size: int = 800,
        chunk_overlap: int = 150
    ) -> List[TextChunk]:
        """Splits document content into structured TextChunks based on format.

        Args:
            content: Raw document string content.
            file_format: Standard suffix/mime type format (e.g. PDF, DOCX, TXT, MD, CSV, JSON).
            chunk_size: Approximate size in characters for text chunks.
            chunk_overlap: Overlapping size between adjacent text chunks.

        Returns:
            List[TextChunk]: List of segmented chunks.
        """
        fmt = file_format.upper().strip(".")
        
        if fmt == "CSV":
            return self._chunk_csv(content)
        elif fmt == "JSON":
            return self._chunk_json(content)
        elif fmt in ("MD", "MARKDOWN"):
            return self._chunk_markdown(content, chunk_size, chunk_overlap)
        else:
            # Default fallback for TXT, PDF, DOCX, HTML
            return self._chunk_text_sliding_window(content, chunk_size, chunk_overlap)

    def _chunk_text_sliding_window(self, content: str, chunk_size: int, chunk_overlap: int) -> List[TextChunk]:
        """Applies character-level sliding window chunking."""
        chunks = []
        if not content:
            return chunks

        # Try splitting by paragraph first, then combine/split to match size
        paragraphs = content.split("\n\n")
        current_chunk = []
        current_len = 0
        chunk_idx = 1
        start_pos = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # If a single paragraph is larger than chunk_size, split it into window chunks
            if len(para) > chunk_size:
                if current_chunk:
                    chunk_text = "\n\n".join(current_chunk)
                    chunks.append(TextChunk(
                        chunk_id=f"chunk-{chunk_idx}",
                        text=chunk_text,
                        section="General",
                        start_char=start_pos,
                        end_char=start_pos + len(chunk_text)
                    ))
                    chunk_idx += 1
                    start_pos += len(chunk_text)
                    current_chunk = []
                    current_len = 0
                
                # Split large paragraph by character sliding window
                step = chunk_size - chunk_overlap
                if step <= 0:
                    step = chunk_size // 2
                for i in range(0, len(para), step):
                    sub_text = para[i:i + chunk_size]
                    chunks.append(TextChunk(
                        chunk_id=f"chunk-{chunk_idx}",
                        text=sub_text,
                        section="General",
                        start_char=start_pos + i,
                        end_char=start_pos + i + len(sub_text)
                    ))
                    chunk_idx += 1
                start_pos += len(para)
            else:
                if current_len + len(para) + 2 > chunk_size and current_chunk:
                    chunk_text = "\n\n".join(current_chunk)
                    chunks.append(TextChunk(
                        chunk_id=f"chunk-{chunk_idx}",
                        text=chunk_text,
                        section="General",
                        start_char=start_pos,
                        end_char=start_pos + len(chunk_text)
                    ))
                    chunk_idx += 1
                    start_pos += len(chunk_text)
                    
                    # Retain overlap (keep the last paragraph in window buffer)
                    overlap_len = len(current_chunk[-1])
                    if overlap_len < chunk_overlap:
                        current_chunk = [current_chunk[-1], para]
                        current_len = overlap_len + len(para) + 2
                    else:
                        current_chunk = [para]
                        current_len = len(para)
                else:
                    current_chunk.append(para)
                    current_len += len(para) + 2

        if current_chunk:
            chunk_text = "\n\n".join(current_chunk)
            chunks.append(TextChunk(
                chunk_id=f"chunk-{chunk_idx}",
                text=chunk_text,
                section="General",
                start_char=start_pos,
                end_char=start_pos + len(chunk_text)
            ))

        return chunks

    def _chunk_markdown(self, content: str, chunk_size: int, chunk_overlap: int) -> List[TextChunk]:
        """Chunks markdown content by splitting on heading sections where possible."""
        chunks = []
        if not content:
            return chunks

        lines = content.splitlines()
        current_section = "Introduction"
        section_lines = []
        chunk_idx = 1
        
        # Simple heading-based section segmenter
        for line in lines:
            if line.startswith("#"):
                # Complete the previous section
                if section_lines:
                    sect_text = "\n".join(section_lines)
                    # Sub-chunk the section if it is too big
                    sub_chunks = self._chunk_text_sliding_window(sect_text, chunk_size, chunk_overlap)
                    for sc in sub_chunks:
                        chunks.append(TextChunk(
                            chunk_id=f"chunk-{chunk_idx}",
                            text=sc.text,
                            section=current_section,
                            start_char=sc.start_char,
                            end_char=sc.end_char
                        ))
                        chunk_idx += 1
                    section_lines = []
                
                # Extract new section header name
                current_section = line.lstrip("#").strip()
            else:
                section_lines.append(line)

        if section_lines:
            sect_text = "\n".join(section_lines)
            sub_chunks = self._chunk_text_sliding_window(sect_text, chunk_size, chunk_overlap)
            for sc in sub_chunks:
                chunks.append(TextChunk(
                    chunk_id=f"chunk-{chunk_idx}",
                    text=sc.text,
                    section=current_section,
                    start_char=sc.start_char,
                    end_char=sc.end_char
                ))
                chunk_idx += 1

        return chunks

    def _chunk_csv(self, content: str) -> List[TextChunk]:
        """Groups CSV records into manageable chunks (e.g. 10 rows per chunk)."""
        chunks = []
        if not content:
            return chunks

        try:
            f = io.StringIO(content.strip())
            reader = csv.reader(f)
            headers = next(reader, None)
            if not headers:
                return chunks
            
            rows = list(reader)
            chunk_size_rows = 10
            chunk_idx = 1
            
            for i in range(0, len(rows), chunk_size_rows):
                group = rows[i:i + chunk_size_rows]
                # Format chunk as subset csv
                out = io.StringIO()
                writer = csv.writer(out)
                writer.writerow(headers)
                writer.writerows(group)
                
                chunks.append(TextChunk(
                    chunk_id=f"chunk-{chunk_idx}",
                    text=out.getvalue(),
                    section=f"Rows {i+1}-{i+len(group)}",
                    start_char=0,
                    end_char=0
                ))
                chunk_idx += 1
        except Exception:
            # Fallback to sliding window on parse errors
            return self._chunk_text_sliding_window(content, 800, 150)
            
        return chunks

    def _chunk_json(self, content: str) -> List[TextChunk]:
        """Chunks JSON content by dividing arrays or breaking nested objects."""
        chunks = []
        if not content:
            return chunks

        try:
            data = json.loads(content)
            chunk_idx = 1
            
            if isinstance(data, list):
                # Chunk list by chunks of 5 items
                step = 5
                for i in range(0, len(data), step):
                    slice_data = data[i:i + step]
                    chunks.append(TextChunk(
                        chunk_id=f"chunk-{chunk_idx}",
                        text=json.dumps(slice_data, indent=2),
                        section=f"Array Slice [{i}:{i+len(slice_data)}]",
                        start_char=0,
                        end_char=0
                    ))
                    chunk_idx += 1
            elif isinstance(data, dict):
                # Chunk dict by keys
                for key, val in data.items():
                    chunks.append(TextChunk(
                        chunk_id=f"chunk-{chunk_idx}",
                        text=json.dumps({key: val}, indent=2),
                        section=f"Key: {key}",
                        start_char=0,
                        end_char=0
                    ))
                    chunk_idx += 1
            else:
                chunks.append(TextChunk(
                    chunk_id="chunk-1",
                    text=content,
                    section="General",
                    start_char=0,
                    end_char=len(content)
                ))
        except Exception:
            return self._chunk_text_sliding_window(content, 800, 150)
            
        return chunks
