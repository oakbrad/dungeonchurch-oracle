#!/usr/bin/env python3
"""
Alignment Classifier for D&D Entities

Implements a behavioral alignment model where stated alignment is a "ceiling"
and actions pull entities away from their stated ideals.

Stages:
1. Stated Alignment Extraction - regex for explicit alignment strings
2. Link Relationship Classification - LLM classifies relationship types
3. Behavioral Alignment Calculation - actions modify alignment
4. Propagation - unclassified entities inherit from connections
"""

import re
import json
import hashlib
import os
from datetime import datetime
from typing import Optional

# Alignment string patterns for explicit extraction
# Matches both full names and abbreviations
ALIGNMENT_PATTERNS = [
    # Full alignment strings (case insensitive)
    (r'\b(lawful\s+good)\b', (1.0, 1.0)),
    (r'\b(neutral\s+good)\b', (0.0, 1.0)),
    (r'\b(chaotic\s+good)\b', (-1.0, 1.0)),
    (r'\b(lawful\s+neutral)\b', (1.0, 0.0)),
    (r'\b(true\s+neutral)\b', (0.0, 0.0)),
    (r'\b(chaotic\s+neutral)\b', (-1.0, 0.0)),
    (r'\b(lawful\s+evil)\b', (1.0, -1.0)),
    (r'\b(neutral\s+evil)\b', (0.0, -1.0)),
    (r'\b(chaotic\s+evil)\b', (-1.0, -1.0)),
    # Abbreviations (case insensitive, word boundaries)
    (r'\bLG\b', (1.0, 1.0)),
    (r'\bNG\b', (0.0, 1.0)),
    (r'\bCG\b', (-1.0, 1.0)),
    (r'\bLN\b', (1.0, 0.0)),
    (r'\bTN\b', (0.0, 0.0)),
    (r'\bN\b(?!\w)', (0.0, 0.0)),  # Just "N" for true neutral, not followed by letter
    (r'\bCN\b', (-1.0, 0.0)),
    (r'\bLE\b', (1.0, -1.0)),
    (r'\bNE\b', (0.0, -1.0)),
    (r'\bCE\b', (-1.0, -1.0)),
]


def compute_content_hash(content: str) -> str:
    """
    Compute SHA256 hash of content for cache keying.
    Uses first 2000 chars for efficiency while maintaining uniqueness.
    """
    truncated = content[:2000] if content else ""
    return hashlib.sha256(truncated.encode('utf-8')).hexdigest()[:16]


def compute_relationship_hash(source_id: str, target_id: str, context: str) -> str:
    """
    Compute hash for relationship cache keying.
    """
    key = f"{source_id}:{target_id}:{context[:500]}"
    return hashlib.sha256(key.encode('utf-8')).hexdigest()[:16]


def load_cache(cache_path: str) -> dict:
    """
    Load alignment cache from file.
    Returns empty structure if file doesn't exist.
    """
    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load cache from {cache_path}: {e}")

    return {
        "entities": {},
        "relationships": {}
    }


def save_cache(cache: dict, cache_path: str) -> None:
    """
    Save alignment cache to file.
    """
    try:
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        with open(cache_path, 'w') as f:
            json.dump(cache, f, indent=2)
    except IOError as e:
        print(f"Warning: Could not save cache to {cache_path}: {e}")


def extract_stated_alignment(content: str) -> Optional[dict]:
    """
    Stage 1: Extract explicitly stated alignment from document content.

    Returns dict with law_chaos and good_evil scores, or None if not found.
    Confidence is 1.0 for explicit statements.
    """
    if not content:
        return None

    content_lower = content.lower()

    for pattern, (law_chaos, good_evil) in ALIGNMENT_PATTERNS:
        if re.search(pattern, content, re.IGNORECASE):
            return {
                "law_chaos": law_chaos,
                "good_evil": good_evil,
                "confidence": 1.0,
                "source": "explicit"
            }

    return None


def classify_relationship_llm(
    source_title: str,
    target_title: str,
    context: str,
    api_key: str,
    cache: dict,
    cache_path: str
) -> Optional[dict]:
    """
    Stage 2: Classify a relationship using LLM.

    Extracts the relationship type and moral/order valence from context.
    Results are cached by relationship hash.
    """
    if not api_key:
        return None

    # Check cache first
    rel_hash = compute_relationship_hash(source_title, target_title, context)
    if rel_hash in cache.get("relationships", {}):
        cached = cache["relationships"][rel_hash]
        return cached.get("result")

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        prompt = f"""Analyze this relationship between two entities in a D&D fantasy setting (the world of Pyora).

Source entity: {source_title}
Target entity: {target_title}
Context: {context}

Classify the relationship and its moral implications. Return a JSON object with:
- "type": the relationship type (e.g., "killed", "saved", "betrayed", "allied", "traded", "helped", "harmed", "employed", "served", "created", "destroyed", "neutral")
- "moral_valence": float from -1.0 (evil act) to 1.0 (good act)
- "order_valence": float from -1.0 (chaotic act) to 1.0 (lawful act)
- "summary": brief 5-10 word description of the relationship

Consider:
- Killing is generally evil, but killing evil creatures for protection is less so
- Betrayal is both evil and chaotic
- Keeping promises and following rules is lawful
- Helping others is good, harming innocents is evil
- Self-interested actions without harming others are neutral

Return ONLY the JSON object, no other text."""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=200
        )

        result_text = response.choices[0].message.content.strip()

        # Parse JSON from response (handle markdown code blocks)
        if result_text.startswith("```"):
            result_text = re.sub(r'^```(?:json)?\n?', '', result_text)
            result_text = re.sub(r'\n?```$', '', result_text)

        result = json.loads(result_text)

        # Validate and clamp values
        result["moral_valence"] = max(-1.0, min(1.0, float(result.get("moral_valence", 0))))
        result["order_valence"] = max(-1.0, min(1.0, float(result.get("order_valence", 0))))

        # Cache the result
        cache.setdefault("relationships", {})[rel_hash] = {
            "result": result,
            "timestamp": datetime.now().isoformat(),
            "source": source_title,
            "target": target_title
        }
        save_cache(cache, cache_path)

        return result

    except Exception as e:
        print(f"Warning: LLM classification failed for {source_title} -> {target_title}: {e}")
        return None


def classify_entity_llm(
    title: str,
    content: str,
    api_key: str,
    cache: dict,
    cache_path: str
) -> Optional[dict]:
    """
    Classify an entity's alignment using LLM when no explicit alignment found.

    Results are cached by content hash.
    """
    if not api_key or not content:
        return None

    # Check cache first
    content_hash = compute_content_hash(content)
    if content_hash in cache.get("entities", {}):
        cached = cache["entities"][content_hash]
        return cached.get("alignment")

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        # Truncate content for API call
        truncated_content = content[:3000] if len(content) > 3000 else content

        prompt = f"""Analyze this entity from a D&D fantasy setting (the world of Pyora) and determine their alignment.

Entity: {title}
Description: {truncated_content}

Return a JSON object with:
- "law_chaos": float from -1.0 (chaotic) to 1.0 (lawful)
- "good_evil": float from -1.0 (evil) to 1.0 (good)
- "confidence": float from 0.0 to 1.0 (how certain you are)
- "reasoning": brief explanation (10-20 words)

Consider:
- Lawful: follows rules, keeps promises, respects hierarchy
- Chaotic: values freedom, breaks rules, unpredictable
- Good: helps others, protects innocents, self-sacrifice
- Evil: harms others, selfish, cruel

If there's not enough information, set confidence low and values near 0.
Return ONLY the JSON object, no other text."""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=150
        )

        result_text = response.choices[0].message.content.strip()

        # Parse JSON from response
        if result_text.startswith("```"):
            result_text = re.sub(r'^```(?:json)?\n?', '', result_text)
            result_text = re.sub(r'\n?```$', '', result_text)

        result = json.loads(result_text)

        alignment = {
            "law_chaos": max(-1.0, min(1.0, float(result.get("law_chaos", 0)))),
            "good_evil": max(-1.0, min(1.0, float(result.get("good_evil", 0)))),
            "confidence": max(0.0, min(1.0, float(result.get("confidence", 0.5)))),
            "source": "llm"
        }

        # Cache the result
        cache.setdefault("entities", {})[content_hash] = {
            "alignment": alignment,
            "timestamp": datetime.now().isoformat(),
            "title": title
        }
        save_cache(cache, cache_path)

        return alignment

    except Exception as e:
        print(f"Warning: LLM entity classification failed for {title}: {e}")
        return None


def calculate_behavioral_alignment(
    stated: Optional[dict],
    relationships: list[dict],
    target_alignments: dict[str, dict]
) -> dict:
    """
    Stage 3: Calculate behavioral alignment from relationships.

    Each relationship impacts alignment based on:
    - The action itself (moral_valence, order_valence)
    - The target's alignment (killing evil vs killing good)

    Returns behavioral alignment scores.
    """
    # Start from stated alignment or neutral
    if stated:
        base_law_chaos = stated["law_chaos"]
        base_good_evil = stated["good_evil"]
    else:
        base_law_chaos = 0.0
        base_good_evil = 0.0

    if not relationships:
        return {
            "law_chaos": base_law_chaos,
            "good_evil": base_good_evil
        }

    # Accumulate action impacts
    total_moral_impact = 0.0
    total_order_impact = 0.0
    total_weight = 0.0

    for rel in relationships:
        if not rel:
            continue

        moral = rel.get("moral_valence", 0)
        order = rel.get("order_valence", 0)

        # Weight by severity (absolute value of impact)
        weight = (abs(moral) + abs(order)) / 2
        if weight < 0.1:
            weight = 0.1  # Minimum weight for any relationship

        # Adjust moral valence based on target's alignment
        target_id = rel.get("target_id")
        if target_id and target_id in target_alignments:
            target_align = target_alignments[target_id]
            target_good_evil = target_align.get("final", {}).get("good_evil", 0)

            # Killing evil is less evil than killing good
            if rel.get("type") in ["killed", "destroyed", "harmed"]:
                # If target is evil (negative), reduce the evil impact
                moral_adjustment = target_good_evil * 0.3  # Up to 30% reduction
                moral = moral - moral_adjustment

        total_moral_impact += moral * weight
        total_order_impact += order * weight
        total_weight += weight

    if total_weight > 0:
        avg_moral = total_moral_impact / total_weight
        avg_order = total_order_impact / total_weight

        # Scale impact (actions have moderate effect, not overwhelming)
        impact_scale = 0.5
        behavioral_good_evil = base_good_evil + (avg_moral * impact_scale)
        behavioral_law_chaos = base_law_chaos + (avg_order * impact_scale)
    else:
        behavioral_good_evil = base_good_evil
        behavioral_law_chaos = base_law_chaos

    # Clamp to valid range
    return {
        "law_chaos": max(-1.0, min(1.0, behavioral_law_chaos)),
        "good_evil": max(-1.0, min(1.0, behavioral_good_evil))
    }


def apply_ceiling_constraint(stated: Optional[dict], behavioral: dict) -> dict:
    """
    Apply the ceiling constraint: entities can't appear better than their stated alignment.

    If stated is Lawful Good (+1, +1), behavioral can only pull toward neutral/evil/chaotic.
    """
    if not stated:
        return behavioral.copy()

    final = behavioral.copy()

    # Can't be more good than stated
    if stated["good_evil"] >= 0:
        final["good_evil"] = min(behavioral["good_evil"], stated["good_evil"])
    else:
        # If stated is evil, can still go more evil
        final["good_evil"] = behavioral["good_evil"]

    # Can't be more lawful than stated
    if stated["law_chaos"] >= 0:
        final["law_chaos"] = min(behavioral["law_chaos"], stated["law_chaos"])
    else:
        # If stated is chaotic, can still go more chaotic
        final["law_chaos"] = behavioral["law_chaos"]

    return final


def calculate_drift(stated: Optional[dict], final: dict) -> float:
    """
    Calculate how far an entity has "drifted" from their stated alignment.

    Returns 0.0 if aligned with stated, up to 1.0 if at opposite extreme.
    """
    if not stated:
        return 0.0

    # Euclidean distance in alignment space, normalized
    law_diff = abs(stated["law_chaos"] - final["law_chaos"])
    good_diff = abs(stated["good_evil"] - final["good_evil"])

    # Max possible distance is 2*sqrt(2) ≈ 2.83 (corner to corner)
    # Normalize to 0-1 range
    distance = (law_diff**2 + good_diff**2) ** 0.5
    max_distance = 2.83

    return min(1.0, distance / max_distance)


def propagate_alignments(nodes: list[dict], links: list[dict], max_iterations: int = 10) -> None:
    """
    Stage 4: Propagate alignments to unclassified entities.

    Entities with no alignment inherit weighted average from connected entities.
    Uses iterative approach similar to PageRank.
    """
    # Build adjacency map
    adjacency = {}
    for link in links:
        source = link.get("source") if isinstance(link.get("source"), str) else link.get("source", {}).get("id")
        target = link.get("target") if isinstance(link.get("target"), str) else link.get("target", {}).get("id")

        if source and target:
            adjacency.setdefault(source, []).append(target)
            adjacency.setdefault(target, []).append(source)

    # Create node lookup
    node_map = {n["id"]: n for n in nodes}

    for iteration in range(max_iterations):
        changes = 0

        for node in nodes:
            if node.get("alignment") is not None:
                continue

            # Get neighbors with alignment
            neighbors = adjacency.get(node["id"], [])
            neighbor_alignments = []

            for neighbor_id in neighbors:
                neighbor = node_map.get(neighbor_id)
                if neighbor and neighbor.get("alignment"):
                    align = neighbor["alignment"]
                    if align.get("final"):
                        neighbor_alignments.append({
                            "law_chaos": align["final"]["law_chaos"],
                            "good_evil": align["final"]["good_evil"],
                            "confidence": align.get("confidence", 0.5)
                        })

            if neighbor_alignments:
                # Weighted average by confidence
                total_weight = sum(a["confidence"] for a in neighbor_alignments)
                if total_weight > 0:
                    avg_law = sum(a["law_chaos"] * a["confidence"] for a in neighbor_alignments) / total_weight
                    avg_good = sum(a["good_evil"] * a["confidence"] for a in neighbor_alignments) / total_weight

                    node["alignment"] = {
                        "stated": None,
                        "behavioral": {"law_chaos": avg_law, "good_evil": avg_good},
                        "final": {"law_chaos": avg_law, "good_evil": avg_good},
                        "confidence": 0.3,  # Low confidence for propagated
                        "drift": 0.0,
                        "source": "propagated"
                    }
                    changes += 1

        if changes == 0:
            break

    print(f"Propagation completed after {iteration + 1} iterations")


def classify_alignments(
    nodes: list[dict],
    links: list[dict],
    alignment_collections: dict[str, str],
    cache_path: str,
    api_key: Optional[str] = None
) -> None:
    """
    Main entry point: Run the full alignment classification pipeline.

    Modifies nodes in-place to add alignment data.

    Args:
        nodes: List of node dicts (must have 'id', 'title', 'content', 'collectionId')
        links: List of link dicts (must have 'source', 'target')
        alignment_collections: Dict mapping collection type to UUID
        cache_path: Path to alignment cache file
        api_key: OpenAI API key (optional, disables LLM if not provided)
    """
    print(f"Starting alignment classification for {len(nodes)} nodes")

    # Load cache
    cache = load_cache(cache_path)

    # Get set of collection IDs that should have alignment
    alignment_collection_ids = set(alignment_collections.values())

    # Build node lookup for relationship classification
    node_map = {n["id"]: n for n in nodes}

    # Stage 1 & 2: Classify each entity
    classified_count = 0
    llm_count = 0
    explicit_count = 0
    skipped_count = 0
    eligible_count = 0

    print(f"Alignment-eligible collection IDs: {alignment_collection_ids}")

    # Debug: check if content is being extracted
    sample_nodes = [n for n in nodes if n.get("collectionId") in alignment_collection_ids][:3]
    for sn in sample_nodes:
        content_len = len(sn.get("content", ""))
        print(f"  Sample node '{sn.get('title', 'unknown')[:30]}': content length = {content_len}")

    for i, node in enumerate(nodes):
        # Skip nodes not in alignment collections
        if node.get("collectionId") not in alignment_collection_ids:
            node["alignment"] = None
            skipped_count += 1
            continue

        eligible_count += 1
        content = node.get("content", "")

        # Stage 1: Try explicit extraction
        stated = extract_stated_alignment(content)

        if stated:
            explicit_count += 1
            node["_stated_alignment"] = stated
            classified_count += 1
            if eligible_count % 50 == 0:
                print(f"  Progress: {eligible_count} eligible nodes processed, {explicit_count} explicit, {llm_count} LLM")
            continue

        # If no explicit alignment and we have API key, try LLM
        if api_key:
            if eligible_count % 10 == 0:
                print(f"  Progress: {eligible_count} eligible nodes, calling LLM for '{node.get('title', 'unknown')[:30]}...'")
            stated = classify_entity_llm(
                node["title"],
                content,
                api_key,
                cache,
                cache_path
            )
            if stated:
                llm_count += 1
                node["_stated_alignment"] = stated
                classified_count += 1
            else:
                node["_stated_alignment"] = None
        else:
            node["_stated_alignment"] = None

    print(f"Stage 1-2 complete:")
    print(f"  - Eligible nodes: {eligible_count}")
    print(f"  - Skipped (wrong collection): {skipped_count}")
    print(f"  - Explicit alignments found: {explicit_count}")
    print(f"  - LLM classifications: {llm_count}")
    print(f"  - Total classified: {classified_count}")

    # Stage 2b: Classify relationships
    # Extract link context from source documents
    relationship_count = 0
    links_processed = 0
    links_with_context = 0

    print(f"\nStage 2b: Classifying relationships ({len(links)} total links)")

    if api_key:
        for link in links:
            links_processed += 1
            if links_processed % 100 == 0:
                print(f"  Progress: {links_processed}/{len(links)} links processed, {relationship_count} relationships classified")

            source_id = link.get("source") if isinstance(link.get("source"), str) else link.get("source", {}).get("id")
            target_id = link.get("target") if isinstance(link.get("target"), str) else link.get("target", {}).get("id")

            source_node = node_map.get(source_id)
            target_node = node_map.get(target_id)

            if not source_node or not target_node:
                continue

            # Only classify relationships involving alignment entities
            if source_node.get("collectionId") not in alignment_collection_ids:
                continue

            # Extract context around the link mention
            content = source_node.get("content", "")
            target_title = target_node.get("title", "")

            # Find context around mention of target
            context = extract_link_context(content, target_title)

            if context:
                links_with_context += 1
                rel = classify_relationship_llm(
                    source_node.get("title", ""),
                    target_title,
                    context,
                    api_key,
                    cache,
                    cache_path
                )

                if rel:
                    rel["source_id"] = source_id
                    rel["target_id"] = target_id
                    link["relationship"] = rel
                    relationship_count += 1

        print(f"Stage 2b complete:")
        print(f"  - Links processed: {links_processed}")
        print(f"  - Links with context found: {links_with_context}")
        print(f"  - Relationships classified: {relationship_count}")
    else:
        print("  Skipping relationship classification (no API key)")

    # Stage 3: Calculate behavioral alignment
    # First pass: collect all stated alignments for target lookup
    target_alignments = {}
    for node in nodes:
        if node.get("_stated_alignment"):
            target_alignments[node["id"]] = {
                "final": node["_stated_alignment"]
            }

    for node in nodes:
        if node.get("alignment") is None and node.get("_stated_alignment") is None:
            continue

        if node.get("collectionId") not in alignment_collection_ids:
            continue

        stated = node.get("_stated_alignment")

        # Gather relationships where this node is the source
        node_relationships = []
        for link in links:
            source_id = link.get("source") if isinstance(link.get("source"), str) else link.get("source", {}).get("id")
            if source_id == node["id"] and link.get("relationship"):
                node_relationships.append(link["relationship"])

        # Calculate behavioral alignment
        behavioral = calculate_behavioral_alignment(stated, node_relationships, target_alignments)

        # Apply ceiling constraint
        final = apply_ceiling_constraint(stated, behavioral)

        # Calculate drift
        drift = calculate_drift(stated, final)

        # Determine confidence
        if stated and stated.get("source") == "explicit":
            confidence = 1.0 - (drift * 0.3)  # Slight reduction if drifted
        elif stated:
            confidence = stated.get("confidence", 0.7)
        else:
            confidence = 0.5

        node["alignment"] = {
            "stated": {"law_chaos": stated["law_chaos"], "good_evil": stated["good_evil"]} if stated else None,
            "behavioral": behavioral,
            "final": final,
            "confidence": confidence,
            "drift": drift,
            "source": stated.get("source", "behavioral") if stated else "behavioral"
        }

        # Clean up temporary field
        if "_stated_alignment" in node:
            del node["_stated_alignment"]

    # Clean up any remaining temporary fields
    for node in nodes:
        if "_stated_alignment" in node:
            del node["_stated_alignment"]

    # Stage 4: Propagate to unclassified entities
    propagate_alignments(nodes, links)

    # Save final cache state
    save_cache(cache, cache_path)

    # Summary
    with_alignment = sum(1 for n in nodes if n.get("alignment") is not None)
    print(f"Alignment classification complete: {with_alignment}/{len(nodes)} nodes have alignment data")


def extract_link_context(content: str, target_title: str, context_chars: int = 200) -> Optional[str]:
    """
    Extract the context around a mention of the target entity in the content.

    Returns the sentence or surrounding text where the target is mentioned.
    """
    if not content or not target_title:
        return None

    # Try to find the target title in the content
    # Handle both exact matches and partial matches
    pattern = re.escape(target_title)
    match = re.search(pattern, content, re.IGNORECASE)

    # Get first word for fallback matching
    first_word = target_title.split()[0] if ' ' in target_title else target_title

    if not match:
        # Try with just the first word if title is multiple words
        if len(first_word) > 3:
            match = re.search(re.escape(first_word), content, re.IGNORECASE)

    if not match:
        return None

    # Extract surrounding context
    start = max(0, match.start() - context_chars)
    end = min(len(content), match.end() + context_chars)

    context = content[start:end]

    # Try to find sentence boundaries
    sentences = re.split(r'[.!?]\s+', context)
    for sentence in sentences:
        if target_title.lower() in sentence.lower() or (len(first_word) > 3 and first_word.lower() in sentence.lower()):
            return sentence.strip()

    return context.strip()


if __name__ == "__main__":
    # Test explicit alignment extraction
    test_cases = [
        ("He is a lawful good paladin.", (1.0, 1.0)),
        ("The creature is chaotic evil.", (-1.0, -1.0)),
        ("Alignment: LG", (1.0, 1.0)),
        ("She considers herself neutral good.", (0.0, 1.0)),
        ("No alignment mentioned here.", None),
    ]

    print("Testing explicit alignment extraction:")
    for text, expected in test_cases:
        result = extract_stated_alignment(text)
        if expected is None:
            status = "✓" if result is None else "✗"
        else:
            status = "✓" if result and (result["law_chaos"], result["good_evil"]) == expected else "✗"
        print(f"  {status} '{text[:40]}...' -> {result}")
