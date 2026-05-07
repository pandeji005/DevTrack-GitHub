/**
 * DevTrack Settings & Profile Logic
 */

document.addEventListener('DOMContentLoaded', () => {
    const btnSaveProfile = document.getElementById('btn-save-profile');
    
    if (btnSaveProfile) {
        btnSaveProfile.addEventListener('click', async () => {
            const bio = document.getElementById('profile-bio').value;
            const twitter = document.getElementById('profile-twitter').value;
            const website = document.getElementById('profile-website').value;
            
            btnSaveProfile.textContent = 'Saving...';
            btnSaveProfile.disabled = true;
            
            try {
                const res = await fetch('/api/profile/update', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        bio: bio,
                        twitter_handle: twitter,
                        website: website
                    })
                });
                
                if (res.ok) {
                    btnSaveProfile.textContent = 'Updated!';
                    setTimeout(() => {
                        btnSaveProfile.textContent = 'Update Identity';
                        btnSaveProfile.disabled = false;
                    }, 2000);
                }
            } catch (err) {
                console.error('Failed to update profile:', err);
                btnSaveProfile.textContent = 'Error';
                btnSaveProfile.disabled = false;
            }
        });
    }
});
