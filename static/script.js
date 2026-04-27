/* ========================================================
   RithuDrive — JavaScript Module
   Modal, Live Pricing, Toasts, Responsive Logic
   ======================================================== */

// ==================== TOAST NOTIFICATIONS ====================
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <span class="toast-icon">ℹ️</span>
        <span>${message}</span>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(20px)';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// ==================== BOOKING MODAL ====================
let currentCarPrice = 0;

function openBookingModal(carName, pricePerDay) {
    currentCarPrice = pricePerDay;
    const modal = document.getElementById('booking-modal');
    if (!modal) return;

    document.getElementById('modal-car-name').textContent = carName;
    document.getElementById('modal-car-price').textContent = `₹${pricePerDay.toLocaleString()} / day`;
    document.getElementById('modal-car-name-input').value = carName;

    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closeBookingModal() {
    const modal = document.getElementById('booking-modal');
    if (modal) {
        modal.classList.remove('active');
        document.body.style.overflow = '';
    }
}

// ==================== LIVE PRICE CALCULATION ====================
async function calculatePrice() {
    const days = parseInt(document.getElementById('modal-days').value) || 0;
    const startDate = document.getElementById('modal-start-date').value;
    const summary = document.getElementById('price-summary');

    if (days < 1 || !startDate) {
        summary.style.display = 'none';
        return;
    }

    try {
        const response = await fetch('/api/calculate_price', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                price_per_day: currentCarPrice,
                days: days,
                start_date: startDate
            })
        });
        
        const data = await response.json();
        
        if (data.total) {
            document.getElementById('price-base').textContent = `₹${data.base.toLocaleString()}`;
            document.getElementById('price-surcharge').textContent = `+₹${data.surcharge.toLocaleString()}`;
            document.getElementById('price-discount').textContent = `-₹${data.discount.toLocaleString()}`;
            document.getElementById('price-total').textContent = `₹${data.total.toLocaleString()}`;
            
            document.getElementById('price-surcharge-row').style.display = data.surcharge > 0 ? 'flex' : 'none';
            document.getElementById('price-discount-row').style.display = data.discount > 0 ? 'flex' : 'none';
            
            summary.style.display = 'block';
        }
    } catch (error) {
        console.error("Price calculation error:", error);
    }
}
