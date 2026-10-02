import re
import hashlib
from typing import List, Set, Iterable

class SimpleMinHash:
    def __init__(self, num_perm: int = 128):
        self.num_perm = num_perm
        self.permutations = self._generate_permutations()

    def _generate_permutations(self) -> List[int]:
        # Simple fixed seeds for hash functions
        return [i * 997 for i in range(1, self.num_perm + 1)]

    def _get_shingles(self, text: str, n: int = 3) -> Set[str]:
        text = re.sub(r'[^\w\s]', '', text.lower())
        tokens = text.split()
        if len(tokens) < n:
            return set([" ".join(tokens)])
        shingles = set()
        for i in range(len(tokens) - n + 1):
            shingles.add(" ".join(tokens[i:i+n]))
        return shingles

    def compute_signature(self, text: str) -> List[int]:
        shingles = self._get_shingles(text)
        signature = [float('inf')] * self.num_perm
        
        for shingle in shingles:
            # Base hash of the shingle
            base_hash = int(hashlib.md5(shingle.encode('utf-8')).hexdigest(), 16)
            for i in range(self.num_perm):
                # Apply permutation
                permuted_hash = (base_hash ^ self.permutations[i]) % (2**32 - 1)
                if permuted_hash < signature[i]:
                    signature[i] = permuted_hash
                    
        return signature
        
    def similarity(self, sig1: List[int], sig2: List[int]) -> float:
        if not sig1 or not sig2:
            return 0.0
        matches = sum(1 for i in range(self.num_perm) if sig1[i] == sig2[i])
        return matches / self.num_perm

class Deduplicator:
    def __init__(self, threshold: float = 0.8):
        self.minhash = SimpleMinHash(num_perm=64)
        self.threshold = threshold
        self.seen_signatures = [] # List of tuples (doc_id, signature)

    def is_duplicate(self, doc_id: str, text: str) -> bool:
        if not text:
            return False
            
        sig = self.minhash.compute_signature(text)
        
        for _, seen_sig in self.seen_signatures:
            sim = self.minhash.similarity(sig, seen_sig)
            if sim >= self.threshold:
                return True
                
        self.seen_signatures.append((doc_id, sig))
        return False
