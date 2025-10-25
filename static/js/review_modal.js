// --- CSRF helper ---
function getCookie(name){
    const m=document.cookie.match('(^|;)\\s*'+name+'\\s*=\\s*([^;]+)');
    return m?m.pop():'';
  }
  const CSRF = getCookie('csrftoken');
  
  // --- open/close ---
  function openReviewModal(coachId){
    document.getElementById('rm-coach-id').value = coachId;
    document.getElementById('rm-rating').value = 0;
    document.getElementById('rm-comment').value = '';
    document.querySelectorAll('#rm-stars .rm-star').forEach(s=>s.classList.remove('active'));
    const m=document.getElementById('review-modal'); 
    m.classList.remove('hidden'); 
    m.classList.add('flex');
  }
  function closeReviewModal(){
    const m=document.getElementById('review-modal'); 
    m.classList.add('hidden'); 
    m.classList.remove('flex');
  }
  
  // --- bind stars ---
  function bindReviewStars(){
    const stars = [...document.querySelectorAll('#rm-stars .rm-star')];
    stars.forEach(btn=>{
      btn.addEventListener('click', ()=>{
        const val = parseInt(btn.dataset.val);
        document.getElementById('rm-rating').value = val;
        stars.forEach(s=>s.classList.toggle('active', parseInt(s.dataset.val) <= val));
      });
    });
  }
  
  // --- submit ---
  async function submitReview(){
    const coachId = document.getElementById('rm-coach-id').value;
    const rating = parseInt(document.getElementById('rm-rating').value || '0');
    const comment = document.getElementById('rm-comment').value.trim();
  
    if(!rating || rating < 1 || rating > 5){
      alert('Please select 1–5 stars.'); 
      return;
    }
  
    const res = await fetch(`/reviews/coach/${coachId}/create/`, {
      method: 'POST',
      headers: { 'Content-Type':'application/json', 'X-CSRFToken': CSRF },
      body: JSON.stringify({ rating, comment })
    });
  
    const data = await res.json().catch(()=> ({}));
    if(!res.ok){
      alert(data.error || 'Failed to submit review');
      return;
    }
  
    // optional: trigger refresh di halaman coach (kalau kamu set global var)
    if(window.reviewListAutoRefresh){ window.loadCoachReviews(window.reviewListAutoRefresh); }
  
    closeReviewModal();
  
    // optional: redirect ke coach profile section reviews
    if(window.afterReviewSubmitted){
      window.afterReviewSubmitted(coachId, data);
    } else {
      alert('Review submitted!');
    }
  }
  
  // --- wire modal buttons on DOM ready ---
  document.addEventListener('DOMContentLoaded', ()=>{
    const m=document.getElementById('review-modal');
    if(!m) return;
    bindReviewStars();
    document.getElementById('rm-cancel').onclick = closeReviewModal;
    document.getElementById('rm-submit').onclick = submitReview;
  });
  
  // expose ke global supaya tombol bisa manggil
  window.openReviewModal = openReviewModal;
  