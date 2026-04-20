// Hageglede Plant Recommendation App - Main JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const postcodeInput = document.getElementById('postcode');
    const effortSlider = document.getElementById('effort-slider');
    const effortValue = document.getElementById('effort-value');
    const getRecommendationsBtn = document.getElementById('get-recommendations');
    const recommendationsContainer = document.getElementById('recommendations-container');
    const myListContainer = document.getElementById('my-list-container');
    const loadingIndicator = document.getElementById('loading-indicator');
    const errorMessage = document.getElementById('error-message');
    
    // State
    let savedPlants = JSON.parse(localStorage.getItem('hageglede_saved_plants') || '{}');
    
    // Initialize effort slider display
    effortSlider.addEventListener('input', function() {
        effortValue.textContent = this.value;
    });
    
    // Load saved plants on page load
    renderSavedPlants();
    
    // Get recommendations button handler
    getRecommendationsBtn.addEventListener('click', function() {
        const postcode = postcodeInput.value.trim();
        const effortLevel = parseInt(effortSlider.value);
        
        // Basic validation
        if (!postcode) {
            showError('Please enter your postcode');
            return;
        }
        
        if (!isValidPostcode(postcode)) {
            showError('Please enter a valid Norwegian postcode (4 digits)');
            return;
        }
        
        if (effortLevel < 1 || effortLevel > 5) {
            showError('Please select an effort level between 1 and 5');
            return;
        }
        
        // Clear previous results and error
        recommendationsContainer.innerHTML = '';
        hideError();
        
        // Show loading
        loadingIndicator.classList.remove('hidden');
        
        // Fetch recommendations from API
        fetch('/api/recommendations', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                postcode: postcode,
                effort_level: effortLevel
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // Hide loading
            loadingIndicator.classList.add('hidden');
            
            // Check if we got recommendations
            if (data.recommendations && data.recommendations.length > 0) {
                renderRecommendations(data.recommendations);
            } else {
                recommendationsContainer.innerHTML = `
                    <div class="no-results">
                        <h3>No plants found for your criteria</h3>
                        <p>Try adjusting the effort level or check if your postcode is correct.</p>
                    </div>
                `;
            }
        })
        .catch(error => {
            // Hide loading
            loadingIndicator.classList.add('hidden');
            
            // Show error
            showError('Could not fetch recommendations. Please try again later.');
            console.error('Fetch error:', error);
        });
    });
    
    // Render plant recommendations
    function renderRecommendations(plants) {
        recommendationsContainer.innerHTML = '';
        
        plants.forEach(plant => {
            const plantCard = createPlantCard(plant, false); // false = not from saved list
            recommendationsContainer.appendChild(plantCard);
        });
    }
    
    // Render saved plants
    function renderSavedPlants() {
        myListContainer.innerHTML = '';
        
        const savedPlantIds = Object.keys(savedPlants);
        
        if (savedPlantIds.length === 0) {
            myListContainer.innerHTML = `
                <div class="no-saved-plants">
                    <p>No saved plants yet</p>
                    <p>Find plants you like and save them here!</p>
                </div>
            `;
            return;
        }
        
        savedPlantIds.forEach(plantId => {
            const plant = savedPlants[plantId];
            const plantCard = createPlantCard(plant, true); // true = from saved list
            myListContainer.appendChild(plantCard);
        });
    }
    
    // Create a plant card element
    function createPlantCard(plant, isSaved) {
        const card = document.createElement('div');
        card.className = 'plant-card';
        card.dataset.id = plant.id;
        
        // Create stars for effort level
        const stars = '★'.repeat(plant.effort_level) + '☆'.repeat(5 - plant.effort_level);
        
        // Create meal ideas list items
        const mealIdeasItems = plant.meal_ideas.map(meal => 
            `<li>${meal}</li>`
        ).join('');
        
        // Determine save button state and icon
        const savedState = savedPlants[plant.id] ? true : isSaved;
        const saveIcon = savedState ? '❤️' : '♡';
        const saveText = savedState ? 'Remove from My List' : 'Save to My List';
        const saveClass = savedState ? 'saved' : '';
        
        card.innerHTML = `
            <div class="card-header">
                <h3 class="plant-name">${plant.name}</h3>
                <button class="save-btn ${saveClass}" data-id="${plant.id}">
                    <span class="save-icon">${saveIcon}</span>
                    <span class="save-text">${saveText}</span>
                </button>
            </div>
            
            <div class="plant-details">
                <div class="plant-image">
                    <img src="${plant.image_url || '/api/placeholder/200/150'}" alt="${plant.name}" onerror="this.src='/api/placeholder/200/150'">
                </div>
                
                <div class="plant-info">
                    <div class="effort-level">
                        <span class="label">Effort Level:</span>
                        <span class="stars">${stars}</span>
                        <span class="level">(${plant.effort_level}/5)</span>
                    </div>
                    
                    <div class="yield-info">
                        <span class="label">Yield:</span>
                        <span class="value">${plant.yield_info || 'Moderate yield'}</span>
                    </div>
                    
                    <div class="growing-season">
                        <span class="label">Season:</span>
                        <span class="value">${plant.growing_season || 'Spring to Fall'}</span>
                    </div>
                    
                    <div class="description">
                        <p>${plant.description || 'A great addition to any garden!'}</p>
                    </div>
                </div>
            </div>
            
            <div class="meal-ideas">
                <h4>Meal Ideas</h4>
                <ul>${mealIdeasItems}</ul>
            </div>
        `;
        
        // Add event listener to save button
        const saveBtn = card.querySelector('.save-btn');
        saveBtn.addEventListener('click', function() {
            const plantId = this.dataset.id;
            toggleSavePlant(plant);
        });
        
        return card;
    }
    
    // Toggle save/unsave plant
    function toggleSavePlant(plant) {
        const plantId = plant.id;
        
        if (savedPlants[plantId]) {
            // Remove from saved plants
            delete savedPlants[plantId];
        } else {
            // Add to saved plants
            savedPlants[plantId] = plant;
        }
        
        // Update localStorage
        localStorage.setItem('hageglede_saved_plants', JSON.stringify(savedPlants));
        
        // Re-render both lists
        renderSavedPlants();
        
        // Update the specific card in recommendations if it exists
        const cardInRecommendations = recommendationsContainer.querySelector(`.plant-card[data-id="${plantId}"] .save-btn`);
        if (cardInRecommendations) {
            const isNowSaved = savedPlants[plantId] ? true : false;
            const saveIcon = isNowSaved ? '❤️' : '♡';
            const saveText = isNowSaved ? 'Remove from My List' : 'Save to My List';
            
            cardInRecommendations.innerHTML = `
                <span class="save-icon">${saveIcon}</span>
                <span class="save-text">${saveText}</span>
            `;
            cardInRecommendations.classList.toggle('saved', isNowSaved);
        }
    }
    
    // Validate Norwegian postcode (4 digits)
    function isValidPostcode(postcode) {
        const postcodeRegex = /^\d{4}$/;
        return postcodeRegex.test(postcode);
    }
    
    // Show error message
    function showError(message) {
        errorMessage.textContent = message;
        errorMessage.classList.remove('hidden');
    }
    
    // Hide error message
    function hideError() {
        errorMessage.classList.add('hidden');
    }
    
    // Event listener for Enter key in postcode field
    postcodeInput.addEventListener('keyup', function(event) {
        if (event.key === 'Enter') {
            getRecommendationsBtn.click();
        }
    });
});