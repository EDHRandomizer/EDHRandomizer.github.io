// ========================================
// CONFIGURATION & CONSTANTS
// ========================================

export const DEFAULT_SETTINGS = {
    timePeriod: 'Monthly',
    minRank: 1,
    maxRank: 1000,
    quantity: 3,
    enableColorFilter: true,
    selectedColors: ['W', 'U', 'B', 'R', 'G'],
    colorMode: 'atmost',
    selectedColorCounts: [],
    excludePartners: true,
    textOutput: false,
    enableAdditionalFilters: false,
    enableCmcFilter: true,
    minCmc: 0,
    maxCmc: 13,
    enableSaltFilter: false,
    saltMode: 'salty', // 'salty' or 'chill'
    enableSetFilter: false,
    includeSets: '',
    excludeSets: '',
    enableAdvancedRandomizer: false,
    distributionEquation: '1'
};

export const CSV_FILES = {
    'Weekly': 'data/top_commanders_week.csv',
    'Monthly': 'data/top_commanders_month.csv',
    '2-Year': 'data/top_commanders_2year.csv'
};

export const COLORS = ['W', 'U', 'B', 'R', 'G'];
