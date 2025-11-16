/**
 * Load testing script using K6 for LuftWay Travel Platform.
 * 
 * Installation:
 *     brew install k6  # macOS
 *     # or download from https://k6.io/docs/getting-started/installation/
 * 
 * Usage:
 *     k6 run backend/tests/load_test_k6.js
 * 
 * With options:
 *     k6 run --vus 100 --duration 30s backend/tests/load_test_k6.js
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { randomIntBetween, randomItem } from 'https://jslib.k6.io/k6-utils/1.2.0/index.js';

export const options = {
    stages: [
        { duration: '30s', target: 50 },   // Ramp up to 50 users
        { duration: '1m', target: 100 },  // Ramp up to 100 users
        { duration: '2m', target: 100 },   // Stay at 100 users
        { duration: '30s', target: 0 },    // Ramp down to 0 users
    ],
    thresholds: {
        http_req_duration: ['p(95)<500'],  // 95% of requests should be below 500ms
        http_req_failed: ['rate<0.01'],    // Error rate should be less than 1%
    },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const destinations = ['Paris', 'Tokyo', 'London', 'New York', 'Dubai', 'Barcelona'];

function getRandomDate(daysFromNow) {
    const date = new Date();
    date.setDate(date.getDate() + daysFromNow);
    return date.toISOString().split('T')[0];
}

export default function () {
    // Search hotels (most common action)
    const destination = randomItem(destinations);
    const checkIn = getRandomDate(randomIntBetween(1, 30));
    const checkOut = getRandomDate(randomIntBetween(31, 37));
    
    const searchParams = {
        destination: destination,
        check_in: checkIn,
        check_out: checkOut,
        guests: randomIntBetween(1, 4),
        rooms: randomIntBetween(1, 2),
        page: randomIntBetween(1, 5),
        page_size: 20,
    };
    
    const searchRes = http.get(`${BASE_URL}/api/v1/search-booking/search`, { params: searchParams });
    check(searchRes, {
        'search status is 200': (r) => r.status === 200,
        'search response time < 1000ms': (r) => r.timings.duration < 1000,
    });
    
    sleep(1);
    
    // Get hotel details (less common)
    if (randomIntBetween(1, 3) === 1) {
        const hotelId = 'a5431bc8-b1c8-4381-9ede-4aa84aeb8d25'; // Replace with actual hotel ID
        const detailsRes = http.get(`${BASE_URL}/api/v1/search-booking/hotels/${hotelId}`);
        check(detailsRes, {
            'hotel details status is 200': (r) => r.status === 200,
            'hotel details response time < 500ms': (r) => r.timings.duration < 500,
        });
        
        sleep(1);
    }
    
    // Health check
    const healthRes = http.get(`${BASE_URL}/health`);
    check(healthRes, {
        'health check status is 200': (r) => r.status === 200,
    });
    
    sleep(randomIntBetween(1, 3));
}

