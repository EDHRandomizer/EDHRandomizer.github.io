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
# - 0.2 (20%) = Moderate-tight variance, noticeable but fair differences (RECOMMENDED)
# - 0.3 (30%) = Moderate variance, more noticeable luck swings
# - 0.5 (50%) = High variance, significant luck swings between players
# - 1.0 (100%) = Extreme variance, wild differences (not recommended)
LUCK_VARIANCE = 0.22

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
                available_perks = perks_by_rarity[preferred_rarity]
                perk_weights = [p.get('weightMultiplier', 1.0) for p in available_perks]
                selected_perk = random.choices(available_perks, weights=perk_weights, k=1)[0]
                return selected_perk
            elif not fallback_allowed:
                return None
        
        # Otherwise, select rarity based on weights
        rarities = list(weights.keys())
        rarity_weights = [weights[r] for r in rarities]
        selected_rarity = random.choices(rarities, weights=rarity_weights, k=1)[0]
        
        # Select random perk from that rarity, weighted by multiplier
        if selected_rarity in perks_by_rarity and perks_by_rarity[selected_rarity]:
            available_perks = perks_by_rarity[selected_rarity]
            
            # Use weightMultiplier if available, default to 1.0
            perk_weights = [p.get('weightMultiplier', 1.0) for p in available_perks]
            
            # Select weighted random perk
            selected_perk = random.choices(available_perks, weights=perk_weights, k=1)[0]
            return selected_perk
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
        Roll perks for a single player using independent probability sampling.
        
        Algorithm:
        1. Roll each perk independently using standard 44/29/17/8 weights
        2. Calculate actual value from rolled perks
        3. Assign luck tier based on distance from expected value
        
        This maintains perfect 44/29/17/8 rarity distribution across all players
        while natural variance creates luck tiers.
        
        Args:
            player_name: Name of the player (for logging)
            perks_count: Number of perks to roll
            max_attempts_multiplier: Unused (kept for API compatibility)
        
        Returns:
            tuple: (perks_list, luck_score)
                - perks_list: List of perk dicts
                - luck_score: Player's actual rolled value (for luck tier display)
        """
        print(f"🎲 Rolling perks for player {player_name}")
        
        # Calculate expected value for reference
        expected_total_value = self.expected_value_per_perk * perks_count
        
        # Roll perks independently - no deduplication
        rolled_perks = []
        for _ in range(perks_count):
            perk = self.get_random_perk()  # Uses 44/29/17/8 weights
            rolled_perks.append(perk)
        
        # Convert to output format
        player_perks = []
        for perk in rolled_perks:
            player_perks.append({
                'id': perk['id'],
                'name': perk['name'],
                'rarity': perk['rarity'],
                'description': perk.get('description', ''),
                'perkPhase': perk.get('perkPhase', 'drafting'),
                'effects': perk.get('effects', {})
            })
        
        # Calculate actual value received (for luck tier display)
        actual_value = sum(self.rarity_values.get(p['rarity'], 1.0) for p in player_perks)
        luck_percentile = (actual_value / expected_total_value) * 100
        print(f"🎲 Final perks for {player_name}: value={actual_value:.2f} (expected: {expected_total_value:.2f}, {luck_percentile:.0f}%)")
        
        return player_perks, actual_value
    
    def roll_perks_for_session(self, session, perks_count):
        """
        Roll perks for all players in a session using per-player independent rolling.
        
        This approach:
        1. Each player rolls perks independently using 44/29/17/8 rarity weights
        2. First selects rarity, then selects perk within that rarity using weightMultiplier
        3. No type deduplication - players can get the same perks
        
        This guarantees:
        - Perfect 44/29/17/8 rarity distribution across all players
        - Mythics can appear regardless of player count
        - Natural variance creates luck tiers automatically
        
        Args:
            session: Session dict with 'players' list
            perks_count: Number of perks to roll per player
        
        Returns:
            Updated session dict with perks assigned to each player
        """
        print(f"🎲 Rolling {perks_count} perks per player for session")
        print(f"🎲 Luck system: variance={LUCK_VARIANCE}, min={LUCK_MIN_MULTIPLIER}x, max={LUCK_MAX_MULTIPLIER}x")
        
        num_players = len(session['players'])
        
        # Get rarity weights
        weights = self.perks_data.get('rarityWeights', {
            'common': 44,
            'uncommon': 29,
            'rare': 17,
            'mythic': 8
        })
        
        print(f"🎲 Expected rarity probabilities:")
        total_weight = sum(weights.values())
        for rarity in ['common', 'uncommon', 'rare', 'mythic']:
            pct = (weights[rarity] / total_weight * 100)
            print(f"   {rarity}: {pct:.1f}%")
        
        # Step 1: Generate luck targets from normal distribution
        expected_total_value = self.expected_value_per_perk * perks_count
        std_dev = expected_total_value * LUCK_VARIANCE
        
        print(f"\n🎲 Rolling perks for {num_players} players...")
        
        # Step 2: Roll perks for each player independently
        for player in session['players']:
            player_name = player.get('name', 'unknown')
            
            # Roll perks using simple independent rolling
            player_perks, actual_value = self.roll_perks_for_player(player_name, perks_count)
            
            player['perks'] = player_perks
        
        # Step 3: Report overall distribution
        print(f"\n🎲 Session complete!")
        all_perks = []
        for player in session['players']:
            all_perks.extend(player.get('perks', []))
        
        rarity_counts = {'common': 0, 'uncommon': 0, 'rare': 0, 'mythic': 0}
        for perk in all_perks:
            rarity_counts[perk['rarity']] += 1
        
        total_perks = len(all_perks)
        print(f"\n🎲 Overall distribution across {num_players} players ({total_perks} total perks):")
        for rarity in ['common', 'uncommon', 'rare', 'mythic']:
            count = rarity_counts[rarity]
            pct = (count / total_perks * 100) if total_perks > 0 else 0
            expected_pct = (weights[rarity] / total_weight * 100)
            print(f"   {rarity}: {count} ({pct:.1f}%, expected {expected_pct:.1f}%)")
        
        return session
    
    def _roll_perks_with_target_value(self, perks_count, luck_target, expected_value, weights, player_name):
        """
        Roll perks for a player using acceptance-rejection to approximate luck target.
        
        Args:
            perks_count: Number of perks to roll
            luck_target: Target total value for this player
            expected_value: Expected total value (for tolerance calculation)
            weights: Rarity weights dict
            player_name: Player name for logging
        
        Returns:
            List of perk dicts
        """
        # Tolerance for acceptance: how close to target we need to be
        # Using wider tolerance to ensure we can always find acceptable combinations
        tolerance = expected_value * 0.4  # Allow ±40% deviation
        
        best_perks = None
        best_distance = float('inf')
        
        max_attempts = 500  # Try many times to find good match
        
        for attempt in range(max_attempts):
            # Roll perks using standard rarity weights
            candidate_perks = []
            used_types = set()
            
            for slot in range(perks_count):
                sub_attempts = 0
                while sub_attempts < 50:
                    perk = self.get_random_perk()  # Uses 44/29/17/8 weights
                    perk_type = self.get_perk_type(perk)
                    
                    if perk_type not in used_types:
                        candidate_perks.append({
                            'id': perk['id'],
                            'name': perk['name'],
                            'rarity': perk['rarity'],
                            'description': perk.get('description', ''),
                            'perkPhase': perk.get('perkPhase', 'drafting'),
                            'effects': perk.get('effects', {})
                        })
                        used_types.add(perk_type)
                        break
                    
                    sub_attempts += 1
                
                # Fallback: if can't find unique type, just add it anyway
                if len(candidate_perks) < slot + 1:
                    candidate_perks.append({
                        'id': perk['id'],
                        'name': perk['name'],
                        'rarity': perk['rarity'],
                        'description': perk.get('description', ''),
                        'perkPhase': perk.get('perkPhase', 'drafting'),
                        'effects': perk.get('effects', {})
                    })
                    used_types.add(self.get_perk_type(perk))
            
            # Calculate total value
            total_value = sum(self.rarity_values.get(p['rarity'], 1.0) for p in candidate_perks)
            distance = abs(total_value - luck_target)
            
            # Accept if within tolerance
            if distance <= tolerance:
                return candidate_perks
            
            # Track best so far
            if distance < best_distance:
                best_distance = distance
                best_perks = candidate_perks
        
        # If we couldn't find perfect match, return best attempt
        return best_perks if best_perks else candidate_perks
    
    def _generate_perk_combinations(self, global_rarity_counts, num_players, perks_count):
        """
        Generate perk combinations that exactly use up the global rarity counts.
        
        This distributes the allocated rarities across players fairly.
        
        Args:
            global_rarity_counts: dict of {rarity: total_count}
            num_players: Number of players
            perks_count: Perks per player
        
        Returns:
            List of perk combinations (each is a list of perk dicts)
        """
        # Create pool of rarity slots
        rarity_slots = []
        for rarity, count in global_rarity_counts.items():
            rarity_slots.extend([rarity] * count)
        
        # Shuffle to randomize distribution
        random.shuffle(rarity_slots)
        
        # Split into chunks for each player
        combinations = []
        for i in range(num_players):
            start_idx = i * perks_count
            end_idx = start_idx + perks_count
            player_rarities = rarity_slots[start_idx:end_idx]
            
            # Roll actual perks for these rarities (with type deduplication)
            player_perks = []
            used_types = set()
            
            for rarity in player_rarities:
                max_attempts = 50
                perk = None
                
                for attempt in range(max_attempts):
                    candidate = self.get_random_perk(preferred_rarity=rarity, fallback_allowed=False)
                    
                    if candidate is None:
                        break
                    
                    perk_type = self.get_perk_type(candidate)
                    
                    if perk_type not in used_types:
                        perk = candidate
                        used_types.add(perk_type)
                        break
                
                # Fallback: if can't find unique type, just take any perk of this rarity
                if perk is None:
                    perk = self.get_random_perk(preferred_rarity=rarity, fallback_allowed=True)
                
                player_perks.append({
                    'id': perk['id'],
                    'name': perk['name'],
                    'rarity': perk['rarity'],
                    'description': perk.get('description', ''),
                    'perkPhase': perk.get('perkPhase', 'drafting'),
                    'effects': perk.get('effects', {})
                })
            
            combinations.append(player_perks)
        
        return combinations
    
    def _select_perks_from_pool_DEPRECATED(self, rarity_pool, perks_count, luck_target, player_name):
        """
        DEPRECATED: This greedy knapsack approach doesn't produce normal distribution.
        Kept for reference only.
        
        Select perks from the global rarity pool that sum close to luck target.
        Uses a greedy knapsack approach with type deduplication.
        
        Args:
            rarity_pool: dict of {rarity: remaining_count}
            perks_count: Number of perks to select
            luck_target: Target total value
            player_name: Player name for logging
        
        Returns:
            List of perk dicts
        """
        selected_perks = []
        used_types = set()
        
        # Calculate target value per slot
        remaining_value = luck_target
        remaining_slots = perks_count
        
        for slot in range(perks_count):
            # Calculate ideal value for this slot
            if remaining_slots > 0:
                target_value = remaining_value / remaining_slots
            else:
                target_value = self.expected_value_per_perk
            
            # Find best available rarity (closest to target, available in pool)
            best_rarity = None
            best_distance = float('inf')
            
            for rarity, count in rarity_pool.items():
                if count > 0:  # Only consider rarities with remaining perks
                    rarity_value = self.rarity_values.get(rarity, 1.0)
                    distance = abs(rarity_value - target_value)
                    
                    if distance < best_distance:
                        best_distance = distance
                        best_rarity = rarity
            
            if best_rarity is None:
                print(f"   ⚠️ No rarities available in pool!")
                break
            
            # Try to get a perk of that rarity (with type deduplication)
            max_attempts = 50
            perk = None
            
            for attempt in range(max_attempts):
                candidate = self.get_random_perk(preferred_rarity=best_rarity, fallback_allowed=False)
                
                if candidate is None:
                    # No perks of this rarity, try next best
                    break
                
                perk_type = self.get_perk_type(candidate)
                
                if perk_type not in used_types:
                    perk = candidate
                    used_types.add(perk_type)
                    break
            
            # Fallback: if can't find unique type, just take any perk of this rarity
            if perk is None:
                perk = self.get_random_perk(preferred_rarity=best_rarity, fallback_allowed=True)
            
            # Add perk and update pool
            selected_perks.append({
                'id': perk['id'],
                'name': perk['name'],
                'rarity': perk['rarity'],
                'description': perk.get('description', ''),
                'perkPhase': perk.get('perkPhase', 'drafting'),
                'effects': perk.get('effects', {})
            })
            
            # Deduct from pool
            perk_rarity = perk['rarity']
            rarity_pool[perk_rarity] -= 1
            
            # Update remaining values
            actual_value = self.rarity_values.get(perk_rarity, 1.0)
            remaining_value -= actual_value
            remaining_slots -= 1
            
            print(f"   Slot {slot+1}: {best_rarity} (value {actual_value:.2f}, remaining: {remaining_value:.2f})")
        
        return selected_perks
    
    def _old_knapsack_implementation(self, rarity_pool, perks_count, luck_target, player_name):
        """
        DEPRECATED: Old implementation kept for reference.
        """
        selected_perks = []
        used_types = set()
        
        # Calculate target value per slot
        remaining_value = luck_target
        remaining_slots = perks_count
        
        for slot in range(perks_count):
            # Calculate ideal value for this slot
            if remaining_slots > 0:
                target_value = remaining_value / remaining_slots
            else:
                target_value = self.expected_value_per_perk
            
            # Find best available rarity (closest to target, available in pool)
            best_rarity = None
            best_distance = float('inf')
            
            for rarity, count in rarity_pool.items():
                if count > 0:  # Only consider rarities with remaining perks
                    rarity_value = self.rarity_values.get(rarity, 1.0)
                    distance = abs(rarity_value - target_value)
                    
                    if distance < best_distance:
                        best_distance = distance
                        best_rarity = rarity
            
            if best_rarity is None:
                print(f"   ⚠️ No rarities available in pool!")
                break
            
            # Try to get a perk of that rarity (with type deduplication)
            max_attempts = 50
            perk = None
            
            for attempt in range(max_attempts):
                candidate = self.get_random_perk(preferred_rarity=best_rarity, fallback_allowed=False)
                
                if candidate is None:
                    # No perks of this rarity, try next best
                    break
                
                perk_type = self.get_perk_type(candidate)
                
                if perk_type not in used_types:
                    perk = candidate
                    used_types.add(perk_type)
                    break
            
            # Fallback: if can't find unique type, just take any perk of this rarity
            if perk is None:
                perk = self.get_random_perk(preferred_rarity=best_rarity, fallback_allowed=True)


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
