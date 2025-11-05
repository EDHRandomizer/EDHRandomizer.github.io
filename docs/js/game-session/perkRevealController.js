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
     * Start the perk reveal - display all cards face down
     * @param {Array} perks - Array of perk objects with {name, rarity, extended_description}
     * @param {Function} onComplete - Callback when all cards are revealed
     */
    async startReveal(perks, onComplete) {
        this.perks = perks;
        this.onComplete = onComplete;
        this.revealedCount = 0;

        // Randomize perk order for surprise factor
        this.perks = this.shuffleArray([...this.perks]);

        // Clear previous reveals
        const container = document.getElementById('perk-cards-container');
        container.innerHTML = '';

        // Display all cards face-down
        this.perks.forEach((perk, index) => {
            this.createPerkCard(perk, index);
        });

        // Continue button stays disabled until all cards are revealed
        this.disableContinueButton();
    }

    /**
     * Shuffle an array using Fisher-Yates algorithm
     * @param {Array} array - Array to shuffle
     * @returns {Array} - Shuffled array
     */
    shuffleArray(array) {
        for (let i = array.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [array[i], array[j]] = [array[j], array[i]];
        }
        return array;
    }

    /**
     * Create a single perk card (face-down)
     * @param {Object} perk - Perk object
     * @param {number} index - Index in the array
     */
    createPerkCard(perk, index) {
        const container = document.getElementById('perk-cards-container');
        
        // Create perk card
        const card = document.createElement('div');
        card.className = `perk-card perk-${perk.rarity}`;
        card.dataset.index = index;
        card.innerHTML = `
            <div class="perk-card-inner">
                <div class="perk-card-front ${perk.rarity}-hint">
                    <div class="card-back-pattern"></div>
                </div>
                <div class="perk-card-back">
                    <div class="perk-name">${perk.name}</div>
                    <div class="perk-card-meta">
                        <div class="perk-rarity-badge">${perk.rarity}</div>
                        ${perk.emoji ? `<div class="perk-card-emoji">${perk.emoji}</div>` : ''}
                    </div>
                    <div class="perk-description">${perk.extended_description || perk.description || ''}</div>
                </div>
            </div>
        `;

        // Add click handler to flip card
        card.addEventListener('click', () => this.flipCard(card, perk));

        container.appendChild(card);
    }

    /**
     * Flip a card when clicked
     * @param {HTMLElement} card - Card element
     * @param {Object} perk - Perk object
     */
    flipCard(card, perk) {
        // Only flip if not already flipped
        if (card.classList.contains('flipped')) {
            return;
        }

        card.classList.add('flipped');
        this.revealedCount++;

        // Add particle effect for rare/mythic
        if (perk.rarity === 'rare' || perk.rarity === 'mythic') {
            setTimeout(() => this.createParticleEffect(card, perk.rarity), 300);
        }

        // Screen shake for mythic
        if (perk.rarity === 'mythic') {
            setTimeout(() => this.screenShake(), 300);
        }

        // Check if all cards are revealed
        if (this.revealedCount >= this.perks.length) {
            this.enableContinueButton();
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
     * Enable the continue button
     */
    enableContinueButton() {
        const continueBtn = document.getElementById('perk-reveal-continue');
        const continueBtnTop = document.getElementById('perk-reveal-continue-top');
        continueBtn.disabled = false;
        continueBtn.classList.add('pulse');
        continueBtnTop.disabled = false;
        continueBtnTop.classList.add('pulse');
    }

    /**
     * Disable the continue button
     */
    disableContinueButton() {
        const continueBtn = document.getElementById('perk-reveal-continue');
        const continueBtnTop = document.getElementById('perk-reveal-continue-top');
        continueBtn.disabled = true;
        continueBtn.classList.remove('pulse');
        continueBtnTop.disabled = true;
        continueBtnTop.classList.remove('pulse');
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
