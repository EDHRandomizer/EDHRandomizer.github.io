/**
 * Pack Configuration Generator for EDH Randomizer Game Mode
 * Converts perk effects into bundle configurations for the pack generator API
 */

export class PackConfigGenerator {
    constructor() {
        // Base standard pack definition (1 expensive, 11 budget, 3 lands)
        this.baseStandardPack = {
            slots: [
                {
                    cardType: "weighted",
                    budget: "expensive",
                    bracket: "any",
                    count: 1
                },
                {
                    cardType: "weighted",
                    budget: "budget",
                    bracket: "any",
                    count: 11
                },
                {
                    cardType: "lands",
                    budget: "any",
                    bracket: "any",
                    count: 3
                }
            ]
        };

        // Special pack templates
        this.specialPackTemplates = {
            gamechanger: {
                name: "Game Changer Pack",
                count: 1,
                slots: [
                    {
                        cardType: "gamechangers",
                        budget: "any",
                        bracket: "any",
                        count: 1
                    }
                ]
            },
            conspiracy: {
                name: "Conspiracy Pack",
                source: "scryfall",
                count: 1,
                useCommanderColorIdentity: true,
                slots: [
                    {
                        query: "https://scryfall.com/search?q=%28t%3Aconspiracy+-is%3Aplaytest%29+OR+%28set%3Amb2+name%3A%22Marchesa%27s+Surprise+Party%22%29+OR+%28set%3Amb2+name%3A%22Rule+with+an+Even+Hand%22%29&unique=cards&as=grid&order=name",
                        count: 1
                    }
                ]
            },
            banned: {
                name: "Banned Cards Pack",
                source: "scryfall",
                count: 1,
                useCommanderColorIdentity: true,
                slots: [
                    {
                        query: "https://scryfall.com/search?q=banned%3Acommander+-f%3Aduel&unique=cards&as=grid&order=name",
                        count: 1
                    }
                ]
            },
            expensive_lands: {
                name: "Expensive Lands Pack",
                source: "scryfall",
                count: 1,
                useCommanderColorIdentity: true,
                slots: [
                    {
                        query: "https://scryfall.com/search?q=t%3Aland+%28o%3A%22add+%7B%22+OR+o%3A%22mana+of+any%22%29+usd%3E10&unique=cards&as=grid&order=usd",
                        count: 1
                    }
                ]
            },
            any_cost_lands: {
                name: "Any Cost Lands Pack",
                source: "scryfall",
                count: 1,
                useCommanderColorIdentity: true,
                slots: [
                    {
                        query: "https://scryfall.com/search?q=t%3Aland+%28o%3A%22add+%7B%22+OR+o%3A%22mana+of+any%22%29&unique=cards&as=grid&order=usd",
                        count: 1
                    }
                ]
            },
            test_cards: {
                name: "Test Cards Pack",
                source: "moxfield",
                count: 1,
                slots: [
                    {
                        moxfieldDeck: "",
                        count: 1
                    }
                ]
            },
            silver_border_cards: {
                name: "Silver-Border Cards Pack",
                source: "moxfield",
                count: 1,
                slots: [
                    {
                        moxfieldDeck: "",
                        count: 1
                    }
                ]
            }
        };
    }

    /**
     * Generate complete bundle config from perk effects
     * @param {Object} perk - perk object with effects
     * @param {string} commanderUrl - Commander URL (for context, not used in config yet)
     * @returns {Object} Bundle configuration for pack generator
     */
    generateBundleConfig(perk, commanderUrl) {
        const bundleConfig = {
            packTypes: []
        };

        if (!perk || !perk.effects) {
            // No perk, return default 5 standard packs
            bundleConfig.packTypes.push({
                count: 5,
                ...JSON.parse(JSON.stringify(this.baseStandardPack))
            });
            return bundleConfig;
        }

        const effects = perk.effects;
        
        // Calculate base pack count (default 5 + extra packs)
        let basePackCount = 5;
        if (effects.packQuantity) {
            basePackCount += effects.packQuantity;
        }

        // Generate standard packs with modifications
        const standardPacks = this.generateStandardPacks(basePackCount, effects);
        bundleConfig.packTypes.push(...standardPacks);

        // Add special packs if specified
        if (effects.specialPack && effects.specialPackCount) {
            const specialPack = this.generateSpecialPack(
                effects.specialPack,
                effects.specialPackCount,
                effects.moxfieldDeck  // Pass Moxfield deck ID
            );
            if (specialPack) {
                bundleConfig.packTypes.push(specialPack);
            }
        }

        return bundleConfig;
    }

    /**
     * Generate standard packs with perk modifications
     * @param {number} totalPacks - Total number of standard packs
     * @param {Object} effects - perk effects
     * @returns {Array} Array of pack type configurations
     */
    generateStandardPacks(totalPacks, effects) {
        const packs = [];

        // Determine how many packs get modifications
        const budgetUpgradePacks = effects.budgetUpgradePacks || 0;
        const fullExpensivePacks = effects.fullExpensivePacks || 0;
        const bracketUpgradePacks = effects.bracketUpgradePacks || 0;
        const bracketUpgrade = effects.bracketUpgrade || null;

        // Calculate pack distribution
        let normalPacks = totalPacks;
        let modifiedPacks = {
            budgetUpgrade: Math.min(budgetUpgradePacks, normalPacks),
            fullExpensive: Math.min(fullExpensivePacks, normalPacks - budgetUpgradePacks),
            bracketUpgrade: Math.min(bracketUpgradePacks, normalPacks - budgetUpgradePacks - fullExpensivePacks)
        };

        normalPacks -= (modifiedPacks.budgetUpgrade + modifiedPacks.fullExpensive + modifiedPacks.bracketUpgrade);

        // Add normal packs
        if (normalPacks > 0) {
            packs.push({
                count: normalPacks,
                ...JSON.parse(JSON.stringify(this.baseStandardPack))
            });
        }

        // Add budget upgraded packs (budget cards become 'any')
        if (modifiedPacks.budgetUpgrade > 0) {
            const budgetType = effects.budgetUpgradeType || 'any';
            const packName = budgetType === 'any' ? 'Any Cost Pack' : 'Full Expensive Pack';
            
            packs.push({
                name: packName,
                count: modifiedPacks.budgetUpgrade,
                slots: [
                    {
                        cardType: "weighted",
                        budget: "expensive",
                        bracket: "any",
                        count: 1
                    },
                    {
                        cardType: "weighted",
                        budget: budgetType === 'any' ? "any" : "expensive",  // Changed from 'budget'
                        bracket: "any",
                        count: 11
                    },
                    {
                        cardType: "lands",
                        budget: "any",
                        bracket: "any",
                        count: 3
                    }
                ]
            });
        }

        // Add full expensive packs
        if (modifiedPacks.fullExpensive > 0) {
            packs.push({
                name: "Full Expensive",
                count: modifiedPacks.fullExpensive,
                slots: [
                    {
                        cardType: "weighted",
                        budget: "expensive",
                        bracket: "any",
                        count: 12  // All 12 cards expensive
                    },
                    {
                        cardType: "lands",
                        budget: "any",
                        bracket: "any",
                        count: 3
                    }
                ]
            });
        }

        // Add bracket upgraded packs
        if (modifiedPacks.bracketUpgrade > 0 && bracketUpgrade) {
            packs.push({
                name: `Bracket ${bracketUpgrade} Pack`,
                count: modifiedPacks.bracketUpgrade,
                slots: [
                    {
                        cardType: "weighted",
                        budget: "expensive",
                        bracket: bracketUpgrade.toString(),
                        count: 1
                    },
                    {
                        cardType: "weighted",
                        budget: "budget",
                        bracket: bracketUpgrade.toString(),
                        count: 11
                    },
                    {
                        cardType: "lands",
                        budget: "any",
                        bracket: "any",
                        count: 3
                    }
                ]
            });
        }

        return packs;
    }

    /**
     * Generate special pack (gamechanger, conspiracy, banned, etc.)
     * @param {string} packType - Type of special pack
     * @param {number} count - Number of cards in the pack
     * @param {string} moxfieldDeck - Moxfield deck ID (optional)
     * @returns {Object|null} Pack configuration or null
     */
    generateSpecialPack(packType, count, moxfieldDeck = null) {
        const template = this.specialPackTemplates[packType];
        if (!template) {
            console.warn(`Unknown special pack type: ${packType}`);
            return null;
        }

        // Clone template
        const pack = JSON.parse(JSON.stringify(template));
        
        // Update count in the slot
        if (pack.slots && pack.slots[0]) {
            pack.slots[0].count = count;
        }
        
        // Add Moxfield deck ID if provided
        if (moxfieldDeck && pack.slots && pack.slots[0]) {
            pack.slots[0].moxfieldDeck = moxfieldDeck;
        }

        return pack;
    }

    /**
     * Validate bundle configuration
     * @param {Object} bundleConfig - Bundle config to validate
     * @returns {Object} { valid: boolean, errors: string[] }
     */
    validateBundleConfig(bundleConfig) {
        const errors = [];

        if (!bundleConfig.packTypes || !Array.isArray(bundleConfig.packTypes)) {
            errors.push('Missing or invalid packTypes array');
            return { valid: false, errors };
        }

        if (bundleConfig.packTypes.length === 0) {
            errors.push('No pack types defined');
            return { valid: false, errors };
        }

        // Validate each pack type
        bundleConfig.packTypes.forEach((pack, index) => {
            if (!pack.slots || !Array.isArray(pack.slots)) {
                errors.push(`Pack ${index}: Missing or invalid slots array`);
            }
            if (pack.count === undefined || pack.count < 1) {
                errors.push(`Pack ${index}: Invalid count`);
            }
        });

        return {
            valid: errors.length === 0,
            errors
        };
    }
}

