/**
 * Perk Loader Module
 * Handles loading perks.json and selecting random perks based on rarity weights
 */

class PerkLoader {
    constructor() {
        this.perks = null;
        this.rarityWeights = null;
    }

    /**
     * Load perks from JSON file
     */
    async loadPerks() {
        if (this.perks) {
            return this.perks;
        }

        try {
            const response = await fetch('/data/perks.json');
            if (!response.ok) {
                throw new Error(`Failed to load perks: ${response.statusText}`);
            }

            const data = await response.json();
            
            // Handle v2.0 format with perkTypes
            if (data.perkTypes) {
                // Flatten all perks from all types into single array
                this.perks = [];
                for (const type of data.perkTypes) {
                    this.perks.push(...type.perks);
                }
            } else {
                // Legacy format
                this.perks = data.perks;
            }
            
            this.rarityWeights = data.rarityWeights;

            return this.perks;
        } catch (error) {
            console.error('Error loading perks:', error);
            throw error;
        }
    }

    /**
     * Get a random perk based on rarity weights
     * Weights: Common 45%, Uncommon 30%, Rare 18%, Mythic 7%
     */
    getRandomPerk() {
        if (!this.perks || !this.rarityWeights) {
            throw new Error('Perks not loaded. Call loadPerks() first.');
        }

        // Calculate total weight
        const totalWeight = Object.values(this.rarityWeights).reduce((sum, weight) => sum + weight, 0);

        // Generate random number
        const random = Math.random() * totalWeight;

        // Determine rarity based on weighted random
        let cumulativeWeight = 0;
        let selectedRarity = null;

        for (const [rarity, weight] of Object.entries(this.rarityWeights)) {
            cumulativeWeight += weight;
            if (random <= cumulativeWeight) {
                selectedRarity = rarity;
                break;
            }
        }

        // Get all perks of the selected rarity
        const perksOfRarity = this.perks.filter(p => p.rarity === selectedRarity);

        if (perksOfRarity.length === 0) {
            console.warn(`No perks found for rarity ${selectedRarity}, falling back to common`);
            const commonPerks = this.perks.filter(p => p.rarity === 'common');
            return commonPerks[Math.floor(Math.random() * commonPerks.length)];
        }

        // Return random perk from that rarity
        return perksOfRarity[Math.floor(Math.random() * perksOfRarity.length)];
    }

    /**
     * Get multiple random perks (for multiple players)
     * @param {number} count - Number of perks to generate
     * @param {boolean} allowDuplicates - Whether to allow duplicate perks
     */
    getRandomPerks(count, allowDuplicates = true) {
        const result = [];

        if (allowDuplicates) {
            for (let i = 0; i < count; i++) {
                result.push(this.getRandomPerk());
            }
        } else {
            // Ensure unique perks
            const available = [...this.perks];
            for (let i = 0; i < count && available.length > 0; i++) {
                const perk = this.getRandomPerk();
                result.push(perk);
                
                // Remove this perk from available pool
                const index = available.findIndex(p => p.id === perk.id);
                if (index !== -1) {
                    available.splice(index, 1);
                }
            }
        }

        return result;
    }

    /**
     * Get perk by ID
     */
    getPerkById(id) {
        if (!this.perks) {
            throw new Error('Perks not loaded. Call loadPerks() first.');
        }

        return this.perks.find(p => p.id === id);
    }

    /**
     * Get all perks of a specific rarity
     */
    getPerksByRarity(rarity) {
        if (!this.perks) {
            throw new Error('Perks not loaded. Call loadPerks() first.');
        }

        return this.perks.filter(p => p.rarity === rarity);
    }
}

// Export both class and singleton instance
export { PerkLoader };
export const perkLoader = new PerkLoader();
