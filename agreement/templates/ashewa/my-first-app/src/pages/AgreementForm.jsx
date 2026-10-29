import React, { useState, useRef, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api, { downloadAuthedFile } from '../api';
import { ACCESS_TOKEN, API_ENDPOINTS } from '../constants';
import '../styles/AgreementForm.css';
import PdfViewer from '../components/PdfViewer';

const initialState = {
  profile_photo: null,
  nationality: '',
  signature: null,
  photo_of_userID: null,
  phone_number: '',
  email_account: '',
  city: '',
  your_name: '',
  father_name: '',
  grand_father_name: '',
  gender: '',
  address: '',
};

const MAX_IMAGE_SIZE = 5 * 1024 * 1024; // 5MB

const AgreementForm = () => {
  const [form, setForm] = useState(initialState);
  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);
  const [backendErrors, setBackendErrors] = useState(null);
  const [profilePreview, setProfilePreview] = useState(null);
  const [userIDPreview, setUserIDPreview] = useState(null);
  const navigate = useNavigate();
  const profileInputRef = useRef();
  const userIDInputRef = useRef();
  const signatureCanvasRef = useRef(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [signatureDataURL, setSignatureDataURL] = useState(null);
  const [agreementTitles, setAgreementTitles] = useState([]);
  const [selectedAgreement, setSelectedAgreement] = useState('');
  const [isPdfViewerOpen, setIsPdfViewerOpen] = useState(false);
  const [currentPdfUrl, setCurrentPdfUrl] = useState('');
  const [myAgreements, setMyAgreements] = useState([]);
  const [loadingMine, setLoadingMine] = useState(true);
  const [downloadingPdf, setDownloadingPdf] = useState(null);

  const nameRegex = /^[a-zA-Z\s]+$/;
  const addressRegex = /^[a-zA-Z0-9\s-.,#]+$/;
  const cityRegex = /^[a-zA-Z\s-]+$/;
  const nationalityRegex = /^[a-zA-Z\s-]+$/;
  const phoneRegex = /^\+?\d{9,15}$/;
  const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)*\.[a-zA-Z]{2,}$/;

  const handleLogout = () => {
    localStorage.removeItem(ACCESS_TOKEN);
    navigate('/login');
  };

  const fetchMyAgreements = async () => {
    try {
      setLoadingMine(true);
      const response = await api.get(API_ENDPOINTS.MY_AGREEMENTS);
      setMyAgreements(Array.isArray(response.data) ? response.data : []);
    } catch (error) {
      console.error('Failed to fetch my agreements:', error);
    } finally {
      setLoadingMine(false);
    }
  };

  useEffect(() => {
    const fetchAgreementTitles = async () => {
      try {
        const response = await api.get('api/pdf_agreement/');
        setAgreementTitles(response.data);
      } catch (error) {
        console.error('Failed to fetch agreement titles:', error);
      }
    };
    fetchAgreementTitles();
    fetchMyAgreements();

    const canvas = signatureCanvasRef.current;
    if (canvas) {
      const ctx = canvas.getContext('2d');
      const setCanvasResolution = () => {
        const rect = canvas.getBoundingClientRect();
        canvas.width = rect.width;
        canvas.height = rect.height;
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.lineCap = 'round';
        ctx.lineWidth = 2;
        ctx.strokeStyle = '#000';
        if (signatureDataURL) {
          const img = new Image();
          img.onload = () => {
            ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
          };
          img.src = signatureDataURL;
        }
      };
      setCanvasResolution();
      window.addEventListener('resize', setCanvasResolution);
      return () => window.removeEventListener('resize', setCanvasResolution);
    }
  }, [signatureDataURL]);

  const getEventCoords = (event) => {
    const canvas = signatureCanvasRef.current;
    const rect = canvas.getBoundingClientRect();
    // Touch events carry client coords on the touches list; mouse events on the event itself.
    const source = event.touches && event.touches[0] ? event.touches[0] : event;
    return {
      x: source.clientX - rect.left,
      y: source.clientY - rect.top,
    };
  };

  const startDrawing = (event) => {
    event.preventDefault(); // stop scrolling while signing on touch devices
    const { x, y } = getEventCoords(event);
    const ctx = signatureCanvasRef.current.getContext('2d');
    ctx.beginPath();
    ctx.moveTo(x, y);
    setIsDrawing(true);
  };

  const draw = (event) => {
    if (!isDrawing) return;
    event.preventDefault();
    const { x, y } = getEventCoords(event);
    const ctx = signatureCanvasRef.current.getContext('2d');
    ctx.lineTo(x, y);
    ctx.stroke();
  };

  const endDrawing = () => {
    setIsDrawing(false);
    const canvas = signatureCanvasRef.current;
    if (canvas) {
      setSignatureDataURL(canvas.toDataURL('image/png'));
    }
  };

  const clearSignature = () => {
    const canvas = signatureCanvasRef.current;
    if (canvas) {
      const ctx = canvas.getContext('2d');
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      setSignatureDataURL(null);
      setForm((prev) => ({ ...prev, signature: null }));
    }
  };

  const validate = () => {
    const newErrors = {};
    if (!selectedAgreement) {
      newErrors.pdf_agreement = 'Please select an agreement.';
    }
    if (!form.profile_photo) newErrors.profile_photo = 'Profile photo is required.';
    else if (!['image/jpeg', 'image/jpg', 'image/png', 'image/gif'].includes(form.profile_photo.type))
      newErrors.profile_photo = 'Profile photo must be JPG, PNG, or GIF.';
    else if (form.profile_photo.size > MAX_IMAGE_SIZE)
      newErrors.profile_photo = 'Profile photo must be less than 5MB.';
    if (!form.your_name || !nameRegex.test(form.your_name) || form.your_name.length < 2)
      newErrors.your_name = 'Valid name (min 2 chars, letters only) required.';
    if (!form.father_name || !nameRegex.test(form.father_name) || form.father_name.length < 2)
      newErrors.father_name = 'Valid father name (min 2 chars, letters only) required.';
    if (!form.grand_father_name || !nameRegex.test(form.grand_father_name) || form.grand_father_name.length < 2)
      newErrors.grand_father_name = 'Valid grand father name (min 2 chars, letters only) required.';
    if (!form.address || form.address.length < 2 || !addressRegex.test(form.address))
      newErrors.address = 'Valid address (min 2 chars) required.';
    if (!form.city || form.city.length < 2 || !cityRegex.test(form.city))
      newErrors.city = 'Valid city required.';
    if (!form.nationality || form.nationality.length < 2 || !nationalityRegex.test(form.nationality))
      newErrors.nationality = 'Valid nationality required.';
    if (!form.phone_number || !phoneRegex.test(form.phone_number))
      newErrors.phone_number = 'Valid phone number (9-15 digits) required.';
    if (!form.email_account || !emailRegex.test(form.email_account))
      newErrors.email_account = 'Valid email address required.';
    if (!form.photo_of_userID) newErrors.photo_of_userID = 'User ID photo is required.';
    else if (!['image/jpeg', 'image/jpg', 'image/png', 'image/gif'].includes(form.photo_of_userID.type))
      newErrors.photo_of_userID = 'User ID photo must be JPG, PNG, or GIF.';
    else if (form.photo_of_userID.size > MAX_IMAGE_SIZE)
      newErrors.photo_of_userID = 'User ID photo must be less than 5MB.';
    if (!form.gender || !['M', 'F'].includes(form.gender))
      newErrors.gender = 'Please select a valid gender (Male or Female).';
    if (!signatureDataURL) newErrors.signature = 'Signature is required.';
    return newErrors;
  };

  const handleChange = (e) => {
    const { name, value, type, files } = e.target;
    if (type === 'file') {
      const file = files[0];
      setForm((prev) => ({ ...prev, [name]: file }));
      if (name === 'profile_photo') {
        setProfilePreview(file ? URL.createObjectURL(file) : null);
      }
      if (name === 'photo_of_userID') {
        setUserIDPreview(file ? URL.createObjectURL(file) : null);
      }
    } else {
      setForm((prev) => ({ ...prev, [name]: value }));
    }
  };

  const handleAgreementSelection = (e) => {
    setSelectedAgreement(e.target.value);
  };

  const handleReadAgreement = () => {
    if (selectedAgreement) {
      const agreement = agreementTitles.find(a => a.id === parseInt(selectedAgreement));
      if (agreement && agreement.pdf_url) {
        setCurrentPdfUrl(agreement.pdf_url); // iframe-safe endpoint
        setIsPdfViewerOpen(true);
      }
    }
  };

  const resetFileInputs = () => {
    if (profileInputRef.current) profileInputRef.current.value = '';
    if (userIDInputRef.current) userIDInputRef.current.value = '';
    setProfilePreview(null);
    setUserIDPreview(null);
    clearSignature();
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrors({});
    setBackendErrors(null);
    const validationErrors = validate();
    if (Object.keys(validationErrors).length > 0) {
      console.log('Frontend validation errors:', validationErrors);
      setErrors(validationErrors);
      setSubmitting(false);
      return;
    }
    setSubmitting(true);
    const token = localStorage.getItem(ACCESS_TOKEN);
    console.log('AgreementForm: Current access token:', token ? 'valid token' : 'no token');
    if (!token) {
      setBackendErrors({ non_field_errors: ['You must be logged in to submit the form.'] });
      console.error('AgreementForm: No access token found');
      navigate('/login');
      setSubmitting(false);
      return;
    }
    const formDataToSend = new FormData();
    for (const key in form) {
      if (form[key] !== null && key !== 'signature') {
        formDataToSend.append(key, form[key]);
      }
    }
    if (signatureDataURL) {
      const signatureBlob = await (await fetch(signatureDataURL)).blob();
      formDataToSend.append('signature', signatureBlob, 'signature.png');
    }
    if (selectedAgreement) {
      formDataToSend.append('pdf_agreement', parseInt(selectedAgreement));
    }

    try {
      const response = await api.post('api/agreement/', formDataToSend, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setSuccess(true);
      setForm(initialState);
      resetFileInputs();
      fetchMyAgreements(); // refresh the list so the new submission appears
    } catch (error) {
      console.error('AgreementForm: Submission error:', error.response ? error.response.data : error.message);
      if (error.response) {
        if (error.response.status === 400) {
          setBackendErrors(error.response.data);
        } else if (error.response.status === 401) {
          setBackendErrors({ non_field_errors: ['Unauthorized: Please log in again.'] });
          navigate('/login');
        } else {
          setBackendErrors({ non_field_errors: ['An error occurred during submission.'] });
        }
      } else {
        setBackendErrors({ non_field_errors: ['Request failed. Please check your connection.'] });
      }
    } finally {
      setSubmitting(false);
    }
  };

  const handleBackToLogin = () => {
    navigate('/login');
  };

  const handleDownloadPdf = async (agreement) => {
    try {
      setDownloadingPdf(agreement.id);
      await downloadAuthedFile(
        `api/agreement/${agreement.id}/pdf/`,
        `agreement_${agreement.id}_${(agreement.your_name || 'summary').replace(/\s+/g, '_')}.pdf`
      );
    } catch (error) {
      console.error('PDF download failed:', error);
    } finally {
      setDownloadingPdf(null);
    }
  };

  const statusClass = (status) =>
    status === 'approved' ? 'status-chip approved' :
    status === 'rejected' ? 'status-chip rejected' : 'status-chip pending';

  if (success) {
    return (
      <div className="form-container">
        <div className="success-message">
          <h2>Thank You!</h2>
          <p>Your agreement has been submitted successfully.</p>
          <p>A confirmation email has been sent to you. You can follow its status under "My Submissions" below.</p>
          <div className="success-buttons">
            <button
              className="back-to-login-btn"
              onClick={() => {
                setSuccess(false);
                setBackendErrors(null);
                setSignatureDataURL(null);
              }}
            >
              Submit Another Agreement
            </button>
            <button className="back-to-login-btn" onClick={handleBackToLogin}>
              Back to Login
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <>
      <nav className="navbar" style={{ height: '50px', width: '100vw' }}>
        <div className="navbar-logo">
          <Link to="/">Digital signature</Link>
        </div>
        <ul className="navbar-links">
          <li>
            <button onClick={handleLogout} className="logout-btn">
              Logout
            </button>
          </li>
        </ul>
      </nav>
      <div className="form-container">
        <form className="agreement-form" onSubmit={handleSubmit} encType="multipart/form-data" aria-live="polite">
          <div className="form-top-header">
            <div className="logo-placeholder">
              <h1 className="logo logoone">
                <a href="/">
                  {process.env.NODE_ENV === 'development' ? (
                    <img
                      src={require('../logo/images.png')}
                      alt="Ashewa Technology Logo"
                      onError={(e) => {
                        e.target.style.display = 'none';
                        console.error('Logo failed to load at ../logo/images.png');
                      }}
                    />
                  ) : (
                    <img
                      src="/static/logo/images.png"
                      alt="Ashewa Technology Logo"
                      onError={(e) => {
                        e.target.style.display = 'none';
                        console.error('Logo failed to load at ../logo/images.png');
                      }}
                    />
                  )}
                </a>
              </h1>
            </div>
            <div className="header-text-section">
              <div className="main-title">Ashewa Technology</div>
            </div>
            <div className="photo-upload-box">
              {profilePreview ? (
                <img src={profilePreview} alt="Profile Preview" className="profile-preview-img" />
              ) : (
                <div className="photo-placeholder-text">Photo Here</div>
              )}
              <input
                ref={profileInputRef}
                type="file"
                required
                name="profile_photo"
                id="profile_photo"
                accept="image/jpeg,image/jpg,image/png,image/gif"
                onChange={handleChange}
                className="hidden-file-input"
                aria-invalid={!!errors.profile_photo}
                aria-describedby="profile_photo_error"
              />
              <label htmlFor="profile_photo" className="upload-photo-label" tabIndex="0" role="button"></label>
              {errors.profile_photo && <span className="error-message" id="profile_photo_error">{errors.profile_photo}</span>}
              {backendErrors?.profile_photo && (
                <span className="error-message" id="profile_photo_backend_error">{backendErrors.profile_photo.join(', ')}</span>
              )}
            </div>
          </div>
          <div className="main-form-title">Agreement Form</div>
          <div className="divider"></div>
          {backendErrors && backendErrors.non_field_errors && (
            <div className="backend-error-message" role="alert">
              {backendErrors.non_field_errors.join(', ')}
            </div>
          )}
          <div className="form-section">
            <div className="form-grid">
              {/* Agreement PDF Selection Section */}
              <h3>Agreement Paper Selection</h3>
              <div className="form-row agreement-selector">
                <label htmlFor="agreement-title">Select an Agreement:</label>
                <select id="agreement-title" value={selectedAgreement} onChange={handleAgreementSelection}>
                  <option value="" disabled>-- Choose an agreement --</option>
                  {agreementTitles.map((agreement) => (
                    <option key={agreement.id} value={agreement.id}>
                      {agreement.type_of_agreement}
                    </option>
                  ))}
                </select>
                <button
                  type="button"
                  onClick={handleReadAgreement}
                  className="read-agreement-btn"
                  disabled={!selectedAgreement}
                >
                  Read
                </button>
                {errors.pdf_agreement && <span className="error-message" id="pdf_agreement_error">{errors.pdf_agreement}</span>}
                {backendErrors?.pdf_agreement && (
                  <span className="error-message" id="pdf_agreement_backend_error">{backendErrors.pdf_agreement.join(', ')}</span>
                )}
              </div>
              {/* Personal Details Section */}
              <h3>Personal Details</h3>
              <div className={`form-row ${errors.your_name ? 'has-error' : ''}`}>
                <label htmlFor="your_name">Your Name:</label>
                <input
                  type="text"
                  required
                  name="your_name"
                  id="your_name"
                  value={form.your_name}
                  onChange={handleChange}
                />
                {errors.your_name && <span className="error-message" id="your_name_error">{errors.your_name}</span>}
                {backendErrors?.your_name && (
                  <span className="error-message" id="your_name_backend_error">{backendErrors.your_name.join(', ')}</span>
                )}
              </div>
              <div className={`form-row ${errors.father_name ? 'has-error' : ''}`}>
                <label htmlFor="father_name">Father's Name:</label>
                <input
                  type="text"
                  required
                  name="father_name"
                  id="father_name"
                  value={form.father_name}
                  onChange={handleChange}
                />
                {errors.father_name && <span className="error-message" id="father_name_error">{errors.father_name}</span>}
                {backendErrors?.father_name && (
                  <span className="error-message" id="father_name_backend_error">{backendErrors.father_name.join(', ')}</span>
                )}
              </div>
              <div className={`form-row ${errors.grand_father_name ? 'has-error' : ''}`}>
                <label htmlFor="grand_father_name">Grand Father's Name:</label>
                <input
                  type="text"
                  required
                  name="grand_father_name"
                  id="grand_father_name"
                  value={form.grand_father_name}
                  onChange={handleChange}
                />
                {errors.grand_father_name && (
                  <span className="error-message" id="grand_father_name_error">{errors.grand_father_name}</span>
                )}
                {backendErrors?.grand_father_name && (
                  <span className="error-message" id="grand_father_name_backend_error">{backendErrors.grand_father_name.join(', ')}</span>
                )}
              </div>
              <div className={`form-row ${errors.gender ? 'has-error' : ''}`}>
                <label htmlFor="gender">Gender:</label>
                <div className="radio-group">
                  <label>
                    <input
                      type="radio"
                      name="gender"
                      value="M"
                      checked={form.gender === 'M'}
                      onChange={handleChange}
                    />
                    Male
                  </label>
                  <label>
                    <input
                      type="radio"
                      name="gender"
                      value="F"
                      checked={form.gender === 'F'}
                      onChange={handleChange}
                    />
                    Female
                  </label>
                </div>
                {errors.gender && <span className="error-message" id="gender_error">{errors.gender}</span>}
                {backendErrors?.gender && (
                  <span className="error-message" id="gender_backend_error">{backendErrors.gender.join(', ')}</span>
                )}
              </div>
              {/* Location Details Section */}
              <h3>Location Details</h3>
              <div className={`form-row ${errors.nationality ? 'has-error' : ''}`}>
                <label htmlFor="nationality">Country:</label>
                <input
                  type="text"
                  required
                  name="nationality"
                  id="nationality"
                  value={form.nationality}
                  onChange={handleChange}
                />
                {errors.nationality && <span className="error-message" id="nationality_error">{errors.nationality}</span>}
                {backendErrors?.nationality && (
                  <span className="error-message" id="nationality_backend_error">{backendErrors.nationality.join(', ')}</span>
                )}
              </div>
              <div className={`form-row ${errors.city ? 'has-error' : ''}`}>
                <label htmlFor="city">City/Town:</label>
                <input
                  type="text"
                  required
                  name="city"
                  id="city"
                  value={form.city}
                  onChange={handleChange}
                />
                {errors.city && <span className="error-message" id="city_error">{errors.city}</span>}
                {backendErrors?.city && (
                  <span className="error-message" id="city_backend_error">{backendErrors.city.join(', ')}</span>
                )}
              </div>
              <div className={`form-row ${errors.address ? 'has-error' : ''}`}>
                <label htmlFor="address">Address:</label>
                <input
                  type="text"
                  required
                  name="address"
                  id="address"
                  value={form.address}
                  onChange={handleChange}
                />
                {errors.address && <span className="error-message" id="address_error">{errors.address}</span>}
                {backendErrors?.address && (
                  <span className="error-message" id="address_backend_error">{backendErrors.address.join(', ')}</span>
                )}
              </div>
              {/* Contact Details Section */}
              <h3>Contact Details</h3>
              <div className={`form-row ${errors.phone_number ? 'has-error' : ''}`}>
                <label htmlFor="phone_number">Phone Number:</label>
                <input
                  type="text"
                  required
                  name="phone_number"
                  id="phone_number"
                  value={form.phone_number}
                  onChange={handleChange}
                />
                {errors.phone_number && <span className="error-message" id="phone_number_error">{errors.phone_number}</span>}
                {backendErrors?.phone_number && (
                  <span className="error-message" id="phone_number_backend_error">{backendErrors.phone_number.join(', ')}</span>
                )}
              </div>
              <div className={`form-row ${errors.email_account ? 'has-error' : ''}`}>
                <label htmlFor="email_account">Email Account:</label>
                <input
                  type="email"
                  name="email_account"
                  id="email_account"
                  required
                  value={form.email_account}
                  onChange={handleChange}
                />
                {errors.email_account && <span className="error-message" id="email_account_error">{errors.email_account}</span>}
                {backendErrors?.email_account && (
                  <span className="error-message" id="email_account_backend_error">{backendErrors.email_account.join(', ')}</span>
                )}
              </div>
              {/* Uploads Section */}
              <h3>Uploads Files</h3>
              <div className={`form-row file-upload-row ${errors.photo_of_userID ? 'has-error' : ''}`}>
                <label htmlFor="photo_of_userID">Photo of User ID:</label>
                <input
                  ref={userIDInputRef}
                  type="file"
                  required
                  name="photo_of_userID"
                  id="photo_of_userID"
                  accept="image/jpeg,image/jpg,image/png,image/gif"
                  onChange={handleChange}
                  className="hidden-file-input"
                  aria-invalid={!!errors.photo_of_userID}
                  aria-describedby="photo_of_userID_error"
                />
                <label htmlFor="photo_of_userID" className="custom-file-upload-button">
                  {userIDPreview ? (
                    <img src={userIDPreview} alt="User ID Preview" className="file-preview-img" />
                  ) : (
                    'Choose File'
                  )}
                </label>
                {errors.photo_of_userID && (
                  <span className="error-message" id="photo_of_userID_error">{errors.photo_of_userID}</span>
                )}
                {backendErrors?.photo_of_userID && (
                  <span className="error-message" id="photo_of_userID_backend_error">{backendErrors.photo_of_userID.join(', ')}</span>
                )}
              </div>
            </div>
          </div>
          <div className="signature-section">
            <div className="signature-title">SIGNATURE</div>
            <div className="signature-content">
              <p>Properly insert your signature.</p>
            </div>
            <div className={`signature-area ${errors.signature ? 'has-error' : ''}`}>
              <div className="signature-canvas-container">
                <canvas
                  ref={signatureCanvasRef}
                  className="signature-canvas"
                  onMouseDown={startDrawing}
                  onMouseUp={endDrawing}
                  onMouseOut={endDrawing}
                  onMouseMove={draw}
                  onTouchStart={startDrawing}
                  onTouchEnd={endDrawing}
                  onTouchCancel={endDrawing}
                  onTouchMove={draw}
                ></canvas>
                <div className="signature-controls">
                  <button type="button" onClick={clearSignature} className="clear-signature-btn">
                    Clear
                  </button>
                </div>
              </div>
              {errors.signature && <span className="error-message" id="signature_error">{errors.signature}</span>}
              {backendErrors?.signature && (
                <span className="error-message" id="signature_backend_error">{backendErrors.signature.join(', ')}</span>
              )}
            </div>
          </div>
          <button className="btn-primary" type="submit" disabled={submitting} aria-busy={submitting}>
            {submitting && <span className="spinner" aria-hidden="true"></span>}
            {submitting ? 'Submitting...' : 'Submit'}
          </button>
        </form>

        {/* My Submissions — lets the signer follow the status of every agreement they submitted */}
        <section className="my-submissions" aria-label="My submissions">
          <div className="submissions-header">
            <h2>My Submissions</h2>
            <button type="button" className="refresh-btn" onClick={fetchMyAgreements} disabled={loadingMine}>
              {loadingMine ? 'Loading…' : '↻ Refresh'}
            </button>
          </div>
          {!loadingMine && myAgreements.length === 0 && (
            <p className="submissions-empty">You haven't submitted any agreements yet. Your submissions and their approval status will appear here.</p>
          )}
          {myAgreements.length > 0 && (
            <div className="submissions-table-wrap">
              <table className="submissions-table">
                <thead>
                  <tr>
                    <th>Agreement</th>
                    <th>Submitted</th>
                    <th>Status</th>
                    <th>Summary PDF</th>
                  </tr>
                </thead>
                <tbody>
                  {myAgreements.map((agreement) => (
                    <tr key={agreement.id}>
                      <td data-label="Agreement">{agreement.pdf_agreement_name || `Agreement #${agreement.id}`}</td>
                      <td data-label="Submitted">
                        {agreement.submited_date ? new Date(agreement.submited_date).toLocaleString() : '—'}
                      </td>
                      <td data-label="Status">
                        <span className={statusClass(agreement.status)}>
                          {(agreement.status_display || agreement.status || 'pending').toUpperCase()}
                        </span>
                      </td>
                      <td data-label="Summary PDF">
                        <button
                          type="button"
                          className="download-pdf-btn"
                          onClick={() => handleDownloadPdf(agreement)}
                          disabled={downloadingPdf === agreement.id}
                        >
                          {downloadingPdf === agreement.id ? 'Preparing…' : 'Download PDF'}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        {/* PDF Viewer Modal */}
        {isPdfViewerOpen && (
          <div className="pdf-viewer-overlay">
            <div className="pdf-viewer-modal-container">
              <button className="close-pdf-btn" onClick={() => setIsPdfViewerOpen(false)}>
                &times;
              </button>
              <PdfViewer pdfUrl={currentPdfUrl} />
            </div>
          </div>
        )}
      </div>
    </>
  );
};

export default AgreementForm;