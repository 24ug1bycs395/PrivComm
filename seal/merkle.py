"""Dependency-free SHA-256 binary Merkle tree helpers."""

import hashlib
from typing import Any


def sha256(data: bytes) -> bytes:
    """Return the SHA-256 digest of data."""
    return hashlib.sha256(data).digest()


def build_merkle_tree(leaves: list[bytes]) -> list[list[bytes]]:
    """Build all Merkle levels, duplicating odd terminal nodes."""
    if not leaves:
        return [[sha256(b"")]]
    levels = [list(leaves)]
    while len(levels[-1]) > 1:
        current = levels[-1]
        if len(current) % 2:
            current = current + [current[-1]]
        levels.append([
            sha256(current[index] + current[index + 1])
            for index in range(0, len(current), 2)
        ])
    return levels


def merkle_root(leaves: list[bytes]) -> bytes:
    """Return the 32-byte Merkle root."""
    return build_merkle_tree(leaves)[-1][0]


def merkle_proof(leaves: list[bytes], index: int) -> list[dict[str, str]]:
    """Return sibling hashes and their positions for a leaf."""
    if index < 0 or index >= len(leaves):
        raise IndexError("Merkle leaf index is out of range")
    proof: list[dict[str, str]] = []
    current = list(leaves)
    position = index
    while len(current) > 1:
        if len(current) % 2:
            current.append(current[-1])
        sibling = position - 1 if position % 2 else position + 1
        proof.append({
            "hash": current[sibling].hex(),
            "position": "left" if position % 2 else "right",
        })
        current = [
            sha256(current[offset] + current[offset + 1])
            for offset in range(0, len(current), 2)
        ]
        position //= 2
    return proof


def verify_proof(leaf: bytes, proof: list[dict[str, Any]], root: bytes) -> bool:
    """Verify a Merkle proof against a root digest."""
    current = leaf
    for item in proof:
        sibling = bytes.fromhex(str(item["hash"]))
        current = (
            sha256(sibling + current)
            if item["position"] == "left"
            else sha256(current + sibling)
        )
    return current == root
