"""
Perk Rolling System
Handles the logic for rolling and assigning perks to players in a session.

Implements a luck-based perk distribution system using normal distribution
to ensure fair but variable perk quality across players.
"""

import json
import os
import time
import random

# === LUCK SYSTEM CONFIGURATION ===
# These constants control how "fair" vs "random" the perk distribution is

# Standard deviation as percentage of expected value (controls bell curve flatness)
# - 0.1 (10%) = Very tight distribution, all players get nearly identical value
# - 0.3 (30%) = Moderate variance, noticeable but fair differences (RECOMMENDED)
# - 0.5 (50%) = High variance, significant luck swings between players
# - 1.0 (100%) = Extreme variance, wild differences (not recommended)
LUCK_VARIANCE = 0.3

# Clamp bounds to prevent absurd extremes (multipliers of expected value)
LUCK_MIN_MULTIPLIER = 0.5   # Minimum: 50% of expected value (prevents terrible luck)
LUCK_MAX_MULTIPLIER = 2.0   # Maximum: 200% of expected value (prevents god-tier luck)

# Rarity value calculation method
# We calculate rarity values as inverse of their drop rates (rarer = more valuable)
# Example with weights {common: 44, uncommon: 29, rare: 17, mythic: 8}:
#   common:    44/44 = 1.00 (baseline)
#   uncommon:  44/29 = 1.52 (52% more valuable than common)
#   rare:      44/17 = 2.59 (159% more valuable than common)
#   mythic:    44/8  = 5.50 (450% more valuable than common)


class PerkRoller:
    """Handles perk rolling logic with luck-based distribution and type-based deduplication"""
    
    def __init__(self, perks_data=None):
        """
        Initialize PerkRoller with perks data
        
        Args:
            perks_data: Optional pre-loaded perks data dict. If None, will load from file.
        """
        self.perks_data = perks_data
        if self.perks_data is None:
            self.perks_data = self._load_perks_data()
        
        # Calculate rarity values based on inverse probability
        self.rarity_values = self._calculate_rarity_values()
        self.expected_value_per_perk = self._calculate_expected_value_per_perk()
        
        print(f"🎲 Perk roller initialized:")
        print(f"   Rarity values: {self.rarity_values}")
        print(f"   Expected value per perk: {self.expected_value_per_perk:.2f}")
    
    def _calculate_rarity_values(self):
        """
        Calculate value for each rarity tier based on inverse probability.
        Rarer perks are worth more.
        
        Returns:
            dict: {rarity: value} where common = 1.0 baseline
        """
        weights = self.perks_data.get('rarityWeights', {
            'common': 44,
            'uncommon': 29,
            'rare': 17,
            'mythic': 8
        })
        
        # Use common as baseline (value = 1.0)
        common_weight = weights.get('common', 44)
        
        return {
            rarity: common_weight / weight
            for rarity, weight in weights.items()
        }
    
    def _calculate_expected_value_per_perk(self):
        """
        Calculate the expected value of a single perk based on rarity distribution.
        This is the weighted average value across all rarities.
        
        Returns:
            float: Expected value (e.g., 1.64 for standard weights)
        """
        weights = self.perks_data.get('rarityWeights', {
            'common': 44,
            'uncommon': 29,
            'rare': 17,
            'mythic': 8
        })
        
        total_weight = sum(weights.values())
        
        # Weighted average: sum(probability * value) for each rarity
        expected_value = sum(
            (weight / total_weight) * self.rarity_values[rarity]
            for rarity, weight in weights.items()
        )
        
        return expected_value
    
    def _load_perks_data(self):
        """Load perks data from JSON file"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        perks_path = os.path.join(current_dir, '..', 'docs', 'data', 'perks.json')
        
        print(f"🎲 Looking for perks.json at: {perks_path}")
        print(f"🎲 Current dir: {current_dir}")
        print(f"🎲 File exists: {os.path.exists(perks_path)}")
        
        try:
            with open(perks_path, 'r', encoding='utf-8') as f:
                perks_data = json.load(f)
            print(f"🎲 Loaded perks.json successfully, version: {perks_data.get('version', 'unknown')}")
            return perks_data
        except FileNotFoundError:
            print(f"⚠️ perks.json not found at {perks_path}, using fallback")
            return {
                'rarityWeights': {'common': 55, 'uncommon': 30, 'rare': 12, 'mythic': 3},
                'perks': []
            }
        except Exception as e:
            print(f"❌ Error loading perks.json: {str(e)}")
            raise
    
    def get_random_perk(self, preferred_rarity=None, fallback_allowed=True):
        """
        Select a random perk based on rarity weights.
        
        Args:
            preferred_rarity: If specified, try to get this rarity first
            fallback_allowed: If True and preferred_rarity not available, use weights
        
        Returns:
            dict: Random perk
        """
        # Get all perks (handle both V1 and V2 format)
        if 'perkTypes' in self.perks_data:
            # V2 format - flatten perkTypes
            all_perks = []
            for ptype in self.perks_data.get('perkTypes', []):
                all_perks.extend(ptype.get('perks', []))
        else:
            # V1 format - direct perks array
            all_perks = self.perks_data.get('perks', [])
        
        if not all_perks:
            raise ValueError("No perks available in perks data")
        
        weights = self.perks_data.get('rarityWeights', {
            'common': 44,
            'uncommon': 29,
            'rare': 17,
            'mythic': 8
        })
        
        # Group perks by rarity
        perks_by_rarity = {}
        for perk in all_perks:
            rarity = perk.get('rarity', 'common')
            if rarity not in perks_by_rarity:
                perks_by_rarity[rarity] = []
            perks_by_rarity[rarity].append(perk)
        
        # If preferred rarity specified, try that first
        if preferred_rarity and preferred_rarity in perks_by_rarity:
            if perks_by_rarity[preferred_rarity]:
                return random.choice(perks_by_rarity[preferred_rarity])
            elif not fallback_allowed:
                return None
        
        # Otherwise, select rarity based on weights
        rarities = list(weights.keys())
        rarity_weights = [weights[r] for r in rarities]
        selected_rarity = random.choices(rarities, weights=rarity_weights, k=1)[0]
        
        # Select random perk from that rarity
        if selected_rarity in perks_by_rarity and perks_by_rarity[selected_rarity]:
            return random.choice(perks_by_rarity[selected_rarity])
        else:
            # Fallback to any perk if selected rarity has no perks
            return random.choice(all_perks)
    

    
    def get_perk_type(self, perk):
        """
        Get the type/category of a perk for deduplication purposes
        
        For example: all "extra commander" perks are the same type,
        all "color filter" perks are the same type, etc.
        """
        # If perk has explicit type, use it
        if 'type' in perk:
            return perk['type']
        
        # Infer type from effects
        effects = perk.get('effects', {})
        
        # Commander quantity perks
        if effects.get('commanderQuantity'):
            return 'commander_quantity'
        
        # Color filter perks
        if effects.get('colorFilterMode'):
            return 'color_filter'
        
        # Distribution shift perks
        if effects.get('distributionShift'):
            return 'distribution_shift'
        
        # Salt mode perks
        if effects.get('saltMode'):
            return 'salt_mode'
        
        # Pack-related perks (drafting phase)
        if perk.get('perkPhase') == 'drafting':
            # Group by pack type if available
            pack_type = effects.get('packType', 'generic_pack')
            return f'pack_{pack_type}'
        
        # Default: use perk ID as unique type (no deduplication)
        return f'unique_{perk["id"]}'
    
    def roll_perks_for_player(self, player_name, perks_count, max_attempts_multiplier=10):
        """
        Roll perks for a single player using constrained multinomial sampling.
        
        Algorithm:
        1. Roll a "luck target" from normal distribution (mean = expected value * count)
        2. Repeatedly roll perks using standard 44/29/17/8 weights
        3. Accept the roll if total value is close to the luck target
        4. Apply type-based deduplication
        
        This maintains the 44/29/17/8 rarity distribution across all players
        while constraining individual player variance using rejection sampling.
        
        Args:
            player_name: Name of the player (for logging)
            perks_count: Number of perks to roll
            max_attempts_multiplier: Max attempts for rejection sampling
        
        Returns:
            tuple: (perks_list, luck_score)
                - perks_list: List of perk dicts
                - luck_score: Player's rolled luck value (for optional display)
        """
        print(f"🎲 Rolling perks for player {player_name}")
        
        # Step 1: Calculate player's luck target using normal distribution
        expected_total_value = self.expected_value_per_perk * perks_count
        std_dev = expected_total_value * LUCK_VARIANCE
        
        # Roll luck target from normal distribution
        luck_target = random.gauss(expected_total_value, std_dev)
        
        # Clamp to prevent absurd extremes
        min_target = expected_total_value * LUCK_MIN_MULTIPLIER
        max_target = expected_total_value * LUCK_MAX_MULTIPLIER
        luck_target = max(min_target, min(luck_target, max_target))
        
        luck_percentile = (luck_target / expected_total_value) * 100
        print(f"🎲   Luck target: {luck_target:.2f} (expected: {expected_total_value:.2f}, {luck_percentile:.0f}%)")
        
        # Step 2: Acceptance-rejection sampling with type deduplication
        # Tolerance: how close to target we need to be
        # Lower tolerance = stricter matching = more attempts needed but better accuracy
        tolerance = expected_total_value * 0.30  # Allow ±30% deviation
        
        best_perks = None
        best_distance = float('inf')
        
        max_attempts = perks_count * max_attempts_multiplier * 10  # More attempts for rejection sampling
        
        for attempt in range(max_attempts):
            # Roll perks using standard weights (44/29/17/8)
            candidate_perks = []
            used_types = set()
            
            # Roll each perk slot
            for slot in range(perks_count):
                sub_attempts = 0
                while sub_attempts < 50:  # Try to avoid duplicate types
                    perk = self.get_random_perk()  # Uses 44/29/17/8 weights
                    perk_type = self.get_perk_type(perk)
                    
                    if perk_type not in used_types:
                        candidate_perks.append(perk)
                        used_types.add(perk_type)
                        break
                    
                    sub_attempts += 1
                
                # Fallback: if we can't find unique type, just add it anyway
                if len(candidate_perks) < slot + 1:
                    candidate_perks.append(perk)
                    used_types.add(self.get_perk_type(perk))
            
            # Calculate total value of this roll
            total_value = sum(self.rarity_values.get(p.get('rarity', 'common'), 1.0) for p in candidate_perks)
            distance = abs(total_value - luck_target)
            
            # Check if this is acceptable (within tolerance)
            if distance <= tolerance:
                print(f"🎲   ✅ Accepted on attempt {attempt + 1}: value={total_value:.2f}, target={luck_target:.2f}, distance={distance:.2f}")
                best_perks = candidate_perks
                break
            
            # Track best so far in case we don't find perfect match
            if distance < best_distance:
                best_distance = distance
                best_perks = candidate_perks
            
            # Every 100 attempts, log progress
            if (attempt + 1) % 100 == 0:
                print(f"🎲   Attempt {attempt + 1}: best distance so far = {best_distance:.2f}")
        
        if best_perks is None:
            print(f"⚠️ Warning: No perks found after {max_attempts} attempts!")
            # Emergency fallback: just roll normally without constraints
            best_perks = []
            for _ in range(perks_count):
                best_perks.append(self.get_random_perk())
        
        # Convert to output format
        player_perks = []
        for perk in best_perks:
            player_perks.append({
                'id': perk['id'],
                'name': perk['name'],
                'rarity': perk['rarity'],
                'description': perk.get('description', ''),
                'perkPhase': perk.get('perkPhase', 'drafting'),
                'effects': perk.get('effects', {})
            })
        
        # Calculate actual value received
        actual_value = sum(self.rarity_values.get(p['rarity'], 1.0) for p in player_perks)
        print(f"🎲 Final perks for {player_name}: {len(player_perks)} (value: {actual_value:.2f} vs target: {luck_target:.2f})")
        
        return player_perks, luck_target
    
    def roll_perks_for_session(self, session, perks_count):
        """
        Roll perks for all players in a session using luck-based distribution
        
        Args:
            session: Session dict with 'players' list
            perks_count: Number of perks to roll per player
        
        Returns:
            Updated session dict with perks assigned to each player
        """
        print(f"🎲 Rolling {perks_count} perks per player for session")
        print(f"🎲 Luck system: variance={LUCK_VARIANCE}, min={LUCK_MIN_MULTIPLIER}x, max={LUCK_MAX_MULTIPLIER}x")
        
        # Track luck scores for logging
        luck_scores = []
        
        for player in session['players']:
            player_perks, luck_score = self.roll_perks_for_player(
                player.get('name', 'unknown'),
                perks_count
            )
            player['perks'] = player_perks
            luck_scores.append((player.get('name', 'unknown'), luck_score))
        
        # Log luck distribution summary
        print(f"\n🎲 Luck Distribution Summary:")
        expected = self.expected_value_per_perk * perks_count
        for name, luck in luck_scores:
            percentile = (luck / expected) * 100
            luck_tier = "🔥 Very Lucky" if percentile >= 130 else \
                       "✨ Lucky" if percentile >= 110 else \
                       "😊 Average" if percentile >= 90 else \
                       "😐 Unlucky" if percentile >= 70 else \
                       "💀 Very Unlucky"
            print(f"   {name}: {luck:.2f} ({percentile:.0f}%) {luck_tier}")
        
        return session


def handle_roll_perks_request(session, player_id):
    """
    Handle the roll perks request for a session
    
    Args:
        session: Session dict
        player_id: ID of the player making the request
    
    Returns:
        tuple: (success: bool, error_code: int or None, error_message: str or None, updated_session: dict or None)
    """
    # Verify host
    if session['hostId'] != player_id:
        return (False, 403, 'Only host can roll perks', None)
    
    # Get perks count from session settings
    perks_count = session.get('settings', {}).get('perksCount', 3)
    print(f"🎲 Rolling {perks_count} perks per player")
    
    # Initialize perk roller and roll perks
    roller = PerkRoller()
    session = roller.roll_perks_for_session(session, perks_count)
    
    # Update session state
    session['state'] = 'selecting'
    session['updated_at'] = time.time()
    print(f"🎲 Updating session with new state: selecting")
    
    return (True, None, None, session)
