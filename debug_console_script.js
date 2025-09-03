
// TEST SCRIPT - Paste this into browser console after API call completes

console.log("🧪 DEBUGGING CARD UPDATE ISSUE");
console.log("===============================");

// 1. Check if cards exist
const cards = document.querySelectorAll('.risk-profile[data-profile]');
console.log(`1. Found ${cards.length} portfolio cards`);

cards.forEach((card, index) => {
    const profile = card.getAttribute('data-profile');
    const isVisible = card.style.display !== 'none';
    console.log(`   Card ${index + 1}: ${profile} (visible: ${isVisible})`);
});

// 2. Check if metric elements exist
const returnElements = document.querySelectorAll('[data-field="expected_return"]');
const riskElements = document.querySelectorAll('[data-field="risk_description"]');
const projectionElements = document.querySelectorAll('[data-field="ten_year_projection"]');

console.log(`\n2. Found metric elements:`);
console.log(`   Expected return elements: ${returnElements.length}`);
console.log(`   Risk elements: ${riskElements.length}`);
console.log(`   Projection elements: ${projectionElements.length}`);

// 3. Check current values
console.log(`\n3. Current values in cards:`);
returnElements.forEach((el, i) => {
    console.log(`   Return ${i + 1}: "${el.textContent}"`);
});

riskElements.forEach((el, i) => {
    console.log(`   Risk ${i + 1}: "${el.textContent}"`);
});

projectionElements.forEach((el, i) => {
    console.log(`   Projection ${i + 1}: "${el.textContent}"`);
});

// 4. Check the optimized portfolios variable
console.log(`\n4. Check optimizedPortfolios variable:`);
console.log('optimizedPortfolios:', window.optimizedPortfolios || 'Not found');

// 5. Check if mock data is being used
console.log(`\n5. Check portfolioConfigs:`);
console.log('portfolioConfigs:', window.portfolioConfigs || 'Not found');

// 6. Manually test the update function
console.log(`\n6. Testing manual update...`);
if (window.optimizedPortfolios && window.optimizedPortfolios.length > 0) {
    const testPortfolio = window.optimizedPortfolios[0];
    const testCard = document.querySelector('.risk-profile[data-profile="conservative"]');
    
    if (testCard && testPortfolio) {
        console.log('Manually calling updateCardMetrics...');
        window.updateCardMetrics(testCard, testPortfolio);
    } else {
        console.log('Missing testCard or testPortfolio:', !!testCard, !!testPortfolio);
    }
} else {
    console.log('No optimizedPortfolios data available');
}

console.log("\n✅ Debug script complete. Check values above!");
