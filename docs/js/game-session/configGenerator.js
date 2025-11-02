/**
 * Config Generator Module
 * Applies perk effects to base pack configuration
 */

class ConfigGenerator {
    constructor() {
        this.baseConfig = {
            slots: [
                {
                    source: "edhrec",
                    bracket: "auto",
                    budgetTier: 2,
                    colorFilter: "commander"
                }
            ]
        };
    }

    /**
     * Generate pack configuration with perk effects applied
     * @param {Object} perk - The perk object
     * @param {string} commanderUrl - EDHRec or Scryfall commander URL
     * @param {number} basePackCount - Base number of packs (default 3)
     */
    generateConfig(perk, commanderUrl, basePackCount = 3) {
        const config = JSON.parse(JSON.stringify(this.baseConfig));
        
        // Start with base pack count
        let packQuantity = basePackCount;
        let budgetTier = config.slots[0].budgetTier;

        // Apply perk effects
        if (perk.effects) {
            const effects = perk.effects;

            // Handle pack quantity modifications
            if (effects.packQuantity) {
                packQuantity += effects.packQuantity;
            }

            // Handle pack quantity override (replaces base count)
            if (effects.packQuantityOverride !== undefined) {
                packQuantity = effects.packQuantityOverride;
            }

            // Handle budget tier shifts
            if (effects.budgetTierShift) {
                budgetTier += effects.budgetTierShift;
                // Clamp budget tier between 0 and 5
                budgetTier = Math.max(0, Math.min(5, budgetTier));
            }

            // Apply color complexity weighting if specified
            if (effects.colorComplexityWeight) {
                config.slots[0].colorComplexityWeight = effects.colorComplexityWeight;
            }

            // Update budget tier in config
            config.slots[0].budgetTier = budgetTier;
        }

        // Return config with metadata
        return {
            commanderUrl: commanderUrl,
            packQuantity: packQuantity,
            config: config,
            perk: {
                id: perk.id,
                name: perk.name,
                rarity: perk.rarity
            }
        };
    }

    /**
     * Validate commander selection against perk restrictions
     * @param {Object} perk - The perk object
     * @param {Object} commanderData - Commander data from EDHRec/Scryfall
     * @returns {Object} - { valid: boolean, reason: string }
     */
    validateCommander(perk, commanderData) {
        if (!powerup.effects) {
            return { valid: true };
        }

        const effects = perk.effects;

        // Check color restrictions
        if (effects.commanderColorRestriction) {
            const colorCount = this.getColorCount(commanderData);
            
            if (effects.commanderColorRestriction === 'mono' && colorCount !== 1) {
                return { valid: false, reason: 'Must select a monocolor commander' };
            }

            if (effects.commanderColorRestriction === 'multicolor') {
                const minColors = effects.minColors || 2;
                if (colorCount < minColors) {
                    return { valid: false, reason: `Must select a commander with ${minColors}+ colors` };
                }
            }
        }

        // Check rank restrictions
        if (effects.commanderRankMax && commanderData.rank > effects.commanderRankMax) {
            return { valid: false, reason: `Commander must be ranked ${effects.commanderRankMax} or better` };
        }

        if (effects.commanderRankMin && commanderData.rank < effects.commanderRankMin) {
            return { valid: false, reason: `Commander must be ranked ${effects.commanderRankMin} or worse` };
        }

        // Check salt restrictions
        if (effects.commanderSaltMin && commanderData.saltScore < effects.commanderSaltMin) {
            return { valid: false, reason: `Commander must have salt score ${effects.commanderSaltMin}+` };
        }

        // Check tribal restriction
        if (effects.commanderRestriction === 'tribal' && !commanderData.tribal) {
            return { valid: false, reason: 'Must select a tribal commander' };
        }

        // Check partner restriction
        if (effects.commanderRestriction === 'partner' && !commanderData.partner) {
            return { valid: false, reason: 'Must select partner commanders' };
        }

        return { valid: true };
    }

    /**
     * Get commander restrictions as human-readable text
     * @param {Object} perk - The perk object
     * @returns {string} - Human-readable restrictions
     */
    getRestrictionText(perk) {
        if (!powerup.effects) {
            return 'None';
        }

        const effects = perk.effects;
        const restrictions = [];

        if (effects.commanderColorRestriction === 'mono') {
            restrictions.push('Monocolor commander only');
        }

        if (effects.commanderColorRestriction === 'multicolor') {
            const minColors = effects.minColors || 2;
            restrictions.push(`${minColors}+ color commander`);
        }

        if (effects.commanderRankMax) {
            restrictions.push(`Ranked top ${effects.commanderRankMax}`);
        }

        if (effects.commanderRankMin) {
            restrictions.push(`Ranked ${effects.commanderRankMin}+`);
        }

        if (effects.commanderSaltMin) {
            restrictions.push(`Salt score ${effects.commanderSaltMin}+`);
        }

        if (effects.commanderRestriction === 'tribal') {
            restrictions.push('Tribal commander');
        }

        if (effects.commanderRestriction === 'partner') {
            restrictions.push('Partner commanders');
        }

        if (effects.randomCommander) {
            restrictions.push('Random commander assigned');
        }

        return restrictions.length > 0 ? restrictions.join(', ') : 'None';
    }

    /**
     * Helper: Get color count from commander data
     */
    getColorCount(commanderData) {
        if (!commanderData.colors || commanderData.colors.length === 0) {
            return 0; // Colorless
        }
        return commanderData.colors.length;
    }

    /**
     * Parse commander URL to extract commander slug
     * @param {string} url - EDHRec or Scryfall URL
     * @returns {string} - Commander slug or null
     */
    parseCommanderUrl(url) {
        try {
            // EDHRec format: https://edhrec.com/commanders/commander-name
            if (url.includes('edhrec.com')) {
                const match = url.match(/\/commanders\/([^/?#]+)/);
                return match ? match[1] : null;
            }

            // Scryfall format: https://scryfall.com/card/set/number/commander-name
            if (url.includes('scryfall.com')) {
                const match = url.match(/\/card\/[^/]+\/[^/]+\/([^/?#]+)/);
                return match ? match[1] : null;
            }

            return null;
        } catch (error) {
            console.error('Error parsing commander URL:', error);
            return null;
        }
    }
}

// Export singleton instance
export const configGenerator = new ConfigGenerator();
