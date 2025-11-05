/**
 * Perk Reveal Controller
 * Handles the animated reveal of perks with dopamine-inducing effects
 */

export class PerkRevealController {
    constructor() {
        this.perks = [];
        this.currentIndex = 0;
        this.isRevealing = false;
        this.skipRequested = false;
        this.onComplete = null;
    }

    /**
     * Start the perk reveal animation
     * @param {Array} perks - Array of perk objects with {name, rarity, description}
     * @param {Function} onComplete - Callback when animation completes
     */
    async startReveal(perks, onComplete) {
        this.perks = perks;
        this.currentIndex = 0;
        this.isRevealing = true;
        this.skipRequested = false;
        this.onComplete = onComplete;

        // Sort perks by rarity (common → uncommon → rare → mythic)
        const rarityOrder = { 'common': 0, 'uncommon': 1, 'rare': 2, 'mythic': 3 };
        this.perks.sort((a, b) => rarityOrder[a.rarity] - rarityOrder[b.rarity]);

        // Clear previous reveals
        const container = document.getElementById('perk-cards-container');
        container.innerHTML = '';

        // Reveal perks one by one
        for (let i = 0; i < this.perks.length; i++) {
            if (this.skipRequested) {
                // Skip animation - show all at once
                this.revealAllRemaining(i);
                break;
            }

            await this.revealPerk(this.perks[i], i);
            this.currentIndex = i + 1;

            // Wait before next reveal
            await this.delay(this.skipRequested ? 0 : 600);
        }

        this.isRevealing = false;

        // Enable continue button after all reveals
        this.enableContinueButton();
    }

    /**
     * Reveal a single perk with animation
     * @param {Object} perk - Perk object
     * @param {number} index - Index in the array
     */
    async revealPerk(perk, index) {
        const container = document.getElementById('perk-cards-container');
        
        // Create perk card
        const card = document.createElement('div');
        card.className = `perk-card perk-${perk.rarity}`;
        card.innerHTML = `
            <div class="perk-card-inner">
                <div class="perk-card-front">
                    <div class="card-back-pattern"></div>
                </div>
                <div class="perk-card-back">
                    <div class="perk-rarity-badge">${perk.rarity}</div>
                    <div class="perk-name">${perk.name}</div>
                    <div class="perk-description">${perk.description}</div>
                </div>
            </div>
        `;

        container.appendChild(card);

        // Trigger flip animation after a brief delay
        await this.delay(50);
        card.classList.add('flipped');

        // Add particle effect for rare/mythic
        if (perk.rarity === 'rare' || perk.rarity === 'mythic') {
            this.createParticleEffect(card, perk.rarity);
        }

        // Screen shake for mythic
        if (perk.rarity === 'mythic') {
            this.screenShake();
        }
    }

    /**
     * Reveal all remaining perks at once (skip animation)
     * @param {number} startIndex - Index to start from
     */
    revealAllRemaining(startIndex) {
        const container = document.getElementById('perk-cards-container');
        
        for (let i = startIndex; i < this.perks.length; i++) {
            const perk = this.perks[i];
            
            const card = document.createElement('div');
            card.className = `perk-card perk-${perk.rarity} flipped instant`;
            card.innerHTML = `
                <div class="perk-card-inner">
                    <div class="perk-card-front">
                        <div class="card-back-pattern"></div>
                    </div>
                    <div class="perk-card-back">
                        <div class="perk-rarity-badge">${perk.rarity}</div>
                        <div class="perk-name">${perk.name}</div>
                        <div class="perk-description">${perk.description}</div>
                    </div>
                </div>
            `;
            
            container.appendChild(card);
        }
    }

    /**
     * Create particle effect around a card
     * @param {HTMLElement} card - Card element
     * @param {string} rarity - Rarity level
     */
    createParticleEffect(card, rarity) {
        const particleCount = rarity === 'mythic' ? 20 : 12;
        const particleContainer = document.createElement('div');
        particleContainer.className = 'particle-container';
        card.appendChild(particleContainer);

        for (let i = 0; i < particleCount; i++) {
            const particle = document.createElement('div');
            particle.className = `particle particle-${rarity}`;
            
            // Random position around card
            const angle = (Math.PI * 2 * i) / particleCount;
            const distance = 80 + Math.random() * 40;
            const x = Math.cos(angle) * distance;
            const y = Math.sin(angle) * distance;
            
            particle.style.setProperty('--tx', `${x}px`);
            particle.style.setProperty('--ty', `${y}px`);
            particle.style.animationDelay = `${Math.random() * 0.3}s`;
            
            particleContainer.appendChild(particle);
        }

        // Remove particles after animation
        setTimeout(() => {
            particleContainer.remove();
        }, 1500);
    }

    /**
     * Screen shake effect
     */
    screenShake() {
        const page = document.getElementById('perk-reveal-page');
        page.classList.add('shake');
        setTimeout(() => {
            page.classList.remove('shake');
        }, 500);
    }

    /**
     * Skip the animation
     */
    skip() {
        this.skipRequested = true;
    }

    /**
     * Replay the reveal animation
     */
    async replay() {
        if (this.isRevealing) return;
        
        this.skipRequested = false;
        const continueBtn = document.getElementById('perk-reveal-continue');
        continueBtn.disabled = true;
        
        await this.startReveal(this.perks, this.onComplete);
    }

    /**
     * Enable the continue button
     */
    enableContinueButton() {
        const continueBtn = document.getElementById('perk-reveal-continue');
        continueBtn.disabled = false;
        continueBtn.classList.add('pulse');
    }

    /**
     * Continue to commander selection
     */
    continue() {
        if (this.onComplete) {
            this.onComplete();
        }
    }

    /**
     * Utility: delay/sleep function
     * @param {number} ms - Milliseconds to delay
     */
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}
