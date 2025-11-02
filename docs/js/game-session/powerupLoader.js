/**
 * Powerup Loader Module
 * Handles loading powerups.json and selecting random powerups based on rarity weights
 */

class PowerupLoader {
    constructor() {
        this.powerups = null;
        this.rarityWeights = null;
    }

    /**
     * Load powerups from JSON file
     */
    async loadPowerups() {
        if (this.powerups) {
            return this.powerups;
        }

        try {
            const response = await fetch('/data/powerups.json');
            if (!response.ok) {
                throw new Error(`Failed to load powerups: ${response.statusText}`);
            }

            const data = await response.json();
            
            // Handle v2.0 format with powerupTypes
            if (data.powerupTypes) {
                // Flatten all powerups from all types into single array
                this.powerups = [];
                for (const type of data.powerupTypes) {
                    this.powerups.push(...type.powerups);
                }
            } else {
                // Legacy format
                this.powerups = data.powerups;
            }
            
            this.rarityWeights = data.rarityWeights;

            return this.powerups;
        } catch (error) {
            console.error('Error loading powerups:', error);
            throw error;
        }
    }

    /**
     * Get a random powerup based on rarity weights
     * Weights: Common 55%, Uncommon 30%, Rare 12%, Mythic 3%
     */
    getRandomPowerup() {
        if (!this.powerups || !this.rarityWeights) {
            throw new Error('Powerups not loaded. Call loadPowerups() first.');
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

        // Get all powerups of the selected rarity
        const powerupsOfRarity = this.powerups.filter(p => p.rarity === selectedRarity);

        if (powerupsOfRarity.length === 0) {
            console.warn(`No powerups found for rarity ${selectedRarity}, falling back to common`);
            const commonPowerups = this.powerups.filter(p => p.rarity === 'common');
            return commonPowerups[Math.floor(Math.random() * commonPowerups.length)];
        }

        // Return random powerup from that rarity
        return powerupsOfRarity[Math.floor(Math.random() * powerupsOfRarity.length)];
    }

    /**
     * Get multiple random powerups (for multiple players)
     * @param {number} count - Number of powerups to generate
     * @param {boolean} allowDuplicates - Whether to allow duplicate powerups
     */
    getRandomPowerups(count, allowDuplicates = true) {
        const result = [];

        if (allowDuplicates) {
            for (let i = 0; i < count; i++) {
                result.push(this.getRandomPowerup());
            }
        } else {
            // Ensure unique powerups
            const available = [...this.powerups];
            for (let i = 0; i < count && available.length > 0; i++) {
                const powerup = this.getRandomPowerup();
                result.push(powerup);
                
                // Remove this powerup from available pool
                const index = available.findIndex(p => p.id === powerup.id);
                if (index !== -1) {
                    available.splice(index, 1);
                }
            }
        }

        return result;
    }

    /**
     * Get powerup by ID
     */
    getPowerupById(id) {
        if (!this.powerups) {
            throw new Error('Powerups not loaded. Call loadPowerups() first.');
        }

        return this.powerups.find(p => p.id === id);
    }

    /**
     * Get all powerups of a specific rarity
     */
    getPowerupsByRarity(rarity) {
        if (!this.powerups) {
            throw new Error('Powerups not loaded. Call loadPowerups() first.');
        }

        return this.powerups.filter(p => p.rarity === rarity);
    }
}

// Export both class and singleton instance
export { PowerupLoader };
export const powerupLoader = new PowerupLoader();
