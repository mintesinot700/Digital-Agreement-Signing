import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation, useParams } from 'react-router-dom';
import { FaChartBar, FaUsers, FaCog, FaUser, FaSignOutAlt, FaSearch, FaBars, FaTimes, FaPlus, FaEdit, FaTrashAlt, FaFilePdf, FaArrowLeft, FaDownload, FaHistory } from 'react-icons/fa';
import api, { downloadAuthedFile } from '../api';
import '../styles/AdminDashboard.css';
import '../styles/PdfAgreement.css';
import '../styles/AgreementDetail.css';
import { ACCESS_TOKEN, REFRESH_TOKEN, IS_ADMIN, API_ENDPOINTS } from '../constants';

// PDF Viewer Component
const PdfViewer = ({ pdfUrl, onClose }) => (
    <div className="pdf-viewer-overlay">
        <div className="pdf-viewer-modal-container">
            <button className="close-pdf-btn" onClick={onClose}>&times;</button>
            <iframe src={pdfUrl} width="100%" height="100%" title="PDF Viewer"></iframe>
        </div>
    </div>
);

const CustomConfirm = ({ message, onConfirm, onCancel }) => (
    <div className="custom-modal-backdrop">
        <div className="custom-modal">
            <div className="custom-modal-content">
                <p>{message}</p>
                <div className="custom-modal-actions">
                    <button onClick={onConfirm} className="confirm-btn">Confirm</button>
                    <button onClick={onCancel} className="cancel-btn">Cancel</button>
                </div>
            </div>
        </div>
    </div>
);

const AdminDashboard = () => {
    const navigate = useNavigate();
    const location = useLocation();
    const { id } = useParams();

    // States from AdminDashboard.js
    const [activeTab, setActiveTab] = useState('agreements');
    const [agreements, setAgreements] = useState([]);
    const [filteredAgreements, setFilteredAgreements] = useState([]);
    const [users, setUsers] = useState([]);
    const [filteredUsers, setFilteredUsers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [agreementSearchTerm, setAgreementSearchTerm] = useState('');
    const [userSearchTerm, setUserSearchTerm] = useState('');
    const [sortOption, setSortOption] = useState('Newest');
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);
    const [isConfirmModalOpen, setIsConfirmModalOpen] = useState(false);
    const [confirmAction, setConfirmAction] = useState(null);
    const [confirmMessage, setConfirmMessage] = useState('');

    // States from PdfAgreement.js
    const [pdfAgreements, setPdfAgreements] = useState([]);
    const [pdfAgreementTitle, setPdfAgreementTitle] = useState('');
    const [pdfAgreementFile, setPdfAgreementFile] = useState(null);
    const [pdfEditingId, setPdfEditingId] = useState(null);
    const [pdfLoading, setPdfLoading] = useState(true);
    const [pdfError, setPdfError] = useState(null);
    const isAdmin = localStorage.getItem(IS_ADMIN) === 'true';

    // States from AgreementDetail.js
    const [agreement, setAgreement] = useState(null);
    const [loadingDetail, setLoadingDetail] = useState(false);
    const [errorDetail, setErrorDetail] = useState('');

    // Audit trail states
    const [auditLogs, setAuditLogs] = useState([]);
    const [auditLoading, setAuditLoading] = useState(false);
    const [statusFilter, setStatusFilter] = useState('');

    // State for PDF viewer modal
    const [isPdfViewerOpen, setIsPdfViewerOpen] = useState(false);
    const [currentPdfUrl, setCurrentPdfUrl] = useState('');

    // --- Functions from AdminDashboard.js ---
    const handleOpenConfirm = (message, action) => {
        setConfirmMessage(message);
        setConfirmAction(() => action);
        setIsConfirmModalOpen(true);
    };

    const handleConfirm = () => {
        if (confirmAction) {
            confirmAction();
        }
        setIsConfirmModalOpen(false);
        setConfirmAction(null);
    };

    const handleCancel = () => {
        setIsConfirmModalOpen(false);
        setConfirmAction(null);
    };

    const handleSortChange = (e) => {
        setSortOption(e.target.value);
    };

    const handleStatusChange = async (agreementId, newStatus) => {
        try {
            setError('');
            await api.patch(`api/agreement/${agreementId}/`, { status: newStatus });
            setAgreements((prevAgreements) =>
                prevAgreements.map((agreement) =>
                    agreement.id === agreementId ? { ...agreement, status: newStatus } : agreement
                )
            );
            setFilteredAgreements((prevFiltered) =>
                prevFiltered.map((agreement) =>
                    agreement.id === agreementId ? { ...agreement, status: newStatus } : agreement
                )
            );
        } catch (err) {
            const errorMessage = err.response ? `Failed to update status: ${err.response.status} ${err.response.statusText}${err.response.data?.detail ? ` - ${err.response.data.detail}` : ''}` : 'Failed to update status. Please try again.';
            setError(errorMessage);
            console.error('Error updating status:', err);
            if (err.response?.status === 401) {
                navigate('/login');
            }
        }
    };

    const handleDeleteAgreement = (agreementId) => {
        handleOpenConfirm(
            'Are you sure you want to delete this agreement?',
            async () => {
                try {
                    setError('');
                    await api.delete(`api/agreement/${agreementId}/`);
                    setAgreements((prevAgreements) => prevAgreements.filter((agreement) => agreement.id !== agreementId));
                    setFilteredAgreements((prevFiltered) => prevFiltered.filter((agreement) => agreement.id !== agreementId));
                } catch (err) {
                    const errorMessage = err.response ? `Failed to delete agreement: ${err.response.status} ${err.response.statusText}${err.response.data?.detail ? ` - ${err.response.data.detail}` : ''}` : 'Failed to delete agreement. Please try again.';
                    setError(errorMessage);
                    console.error('Error deleting agreement:', err);
                    if (err.response?.status === 401) {
                        navigate('/login');
                    }
                }
            }
        );
    };

    const handleDeleteUser = (userId) => {
        handleOpenConfirm(
            'Are you sure you want to delete this user?',
            async () => {
                try {
                    setError('');
                    await api.delete(`api/users/${userId}/`);
                    setUsers((prevUsers) => prevUsers.filter((user) => user.id !== userId));
                    setFilteredUsers((prevFiltered) => prevFiltered.filter((user) => user.id !== userId));
                } catch (err) {
                    const errorMessage = err.response ? `Failed to delete user: ${err.response.status} ${err.response.statusText}${err.response.data?.detail ? ` - ${err.response.data.detail}` : ''}` : 'Failed to delete user. Please try again.';
                    setError(errorMessage);
                    console.error('Error deleting user:', err);
                    if (err.response?.status === 401) {
                        navigate('/login');
                    }
                }
            }
        );
    };

    const handleTabClick = (tab) => {
        setIsSidebarOpen(false);
        setActiveTab(tab);
        navigate(`/admin/dashboard?tab=${tab}`);
    };

    const handleLogout = () => {
        setIsSidebarOpen(false);
        navigate('/logout'); // Redirect to the new dedicated logout route
    };
    
    // --- Functions from PdfAgreement.js ---
    const getPdfAgreements = async () => {
        try {
            const res = await api.get('/api/pdf_agreement/');
            const sortedAgreements = res.data.sort((a, b) => b.id - a.id);
            setPdfAgreements(sortedAgreements);
            setPdfLoading(false);
        } catch (error) {
            console.error('Failed to fetch PDF agreements:', error);
            setPdfError('Failed to load agreements.');
            setPdfLoading(false);
        }
    };

    const handlePdfTitleChange = (e) => {
        setPdfAgreementTitle(e.target.value);
    };

    const handlePdfFileChange = (e) => {
        setPdfAgreementFile(e.target.files[0]);
    };

    const handlePdfUpload = async (e) => {
        e.preventDefault();
        const formData = new FormData();
        formData.append('type_of_agreement', pdfAgreementTitle);
        if (pdfAgreementFile) {
            formData.append('pdf_file', pdfAgreementFile);
        }

        try {
            if (pdfEditingId) {
                await api.patch(`/api/pdf_agreement/${pdfEditingId}/`, formData, {
                    headers: { 'Content-Type': 'multipart/form-data' },
                });
            } else {
                await api.post('/api/pdf_agreement/create/', formData, {
                    headers: { 'Content-Type': 'multipart/form-data' },
                });
            }
            setPdfAgreementTitle('');
            setPdfAgreementFile(null);
            setPdfEditingId(null);
            setActiveTab('pdf-agreements');
            getPdfAgreements();
        } catch (error) {
            console.error('Failed to upload/edit PDF agreement:', error);
            alert('Failed to save agreement. Please check your inputs and try again.');
        }
    };

    const handlePdfEdit = (id) => {
        const agreementToEdit = pdfAgreements.find(agreement => agreement.id === id);
        if (agreementToEdit) {
            setPdfAgreementTitle(agreementToEdit.type_of_agreement);
            setPdfEditingId(id);
            setActiveTab('pdf-upload');
        }
    };

    const handlePdfDelete = async (id) => {
        if (window.confirm('Are you sure you want to delete this agreement?')) {
            try {
                await api.delete(`/api/pdf_agreement/${id}/`);
                getPdfAgreements();
            } catch (error) {
                console.error('Failed to delete PDF agreement:', error);
                alert('Failed to delete agreement.');
            }
        }
    };

    const handleViewPdf = (pdfUrl) => {
        setCurrentPdfUrl(pdfUrl);
        setIsPdfViewerOpen(true);
    };

    const handleGoBack = () => {
        setActiveTab('pdf-agreements');
        setPdfAgreementTitle('');
        setPdfAgreementFile(null);
        setPdfEditingId(null);
    };

    // --- Functions from AgreementDetail.js ---
    const fetchAgreementDetail = async (agreementId) => {
        setLoadingDetail(true);
        setErrorDetail('');
        try {
            const res = await api.get(`/api/agreement/${agreementId}/`);
            setAgreement(res.data);
        } catch (err) {
            setErrorDetail(err.message || 'Failed to fetch agreement details.');
            console.error('Error fetching agreement details:', err);
        } finally {
            setLoadingDetail(false);
        }
    };
    
    // --- useEffect Hooks ---
    useEffect(() => {
        const fetchData = async () => {
            try {
                console.log('Fetching agreements and users');
                const [agreementsRes, usersRes] = await Promise.all([
                    api.get(API_ENDPOINTS.AGREEMENT_LIST || 'api/agreement_list/'),
                    api.get(API_ENDPOINTS.USER_LIST || 'api/UserListView/'),
                ]);

                const agreementsWithStatus = (Array.isArray(agreementsRes.data) ? agreementsRes.data : []).map((ag) => ({
                    ...ag,
                    submitted: ag.submited_date ? new Date(ag.submited_date) : null,
                    status: (ag.status || 'pending').toLowerCase(),
                }));

                setAgreements(agreementsWithStatus);
                setFilteredAgreements(agreementsWithStatus);
                setUsers(Array.isArray(usersRes.data) ? usersRes.data : []);
                setFilteredUsers(Array.isArray(usersRes.data) ? usersRes.data : []);
            } catch (err) {
                const errorMessage = err.response ? `Failed to load data: ${err.response.status} ${err.response.statusText}${err.response.data?.detail ? ` - ${err.response.data.detail}` : ''}` : 'Failed to load dashboard data. Please ensure the backend is running and you are authenticated.';
                setError(errorMessage);
                console.error('Error fetching data:', err);
                if (err.response?.status === 401) {
                    navigate('/login');
                }
            } finally {
                setLoading(false);
            }
        };

        if (!localStorage.getItem(ACCESS_TOKEN) || localStorage.getItem(IS_ADMIN) !== 'true') {
            console.log('No access token or not admin, redirecting to login');
            navigate('/login');
            return;
        }

        fetchData();
        getPdfAgreements();
    }, [navigate]);

    useEffect(() => {
        const params = new URLSearchParams(location.search);
        const tabParam = params.get('tab');
        if (tabParam && ['agreements', 'users', 'pdf-agreements', 'pdf-upload', 'audit'].includes(tabParam)) {
            setActiveTab(tabParam);
        }
    }, [location.search]);

    useEffect(() => {
        const lowerCaseSearchTerm = agreementSearchTerm.toLowerCase();
        const filtered = agreements.filter(
            (agreement) =>
                (agreement.phone_number || '').toLowerCase().includes(lowerCaseSearchTerm) ||
                (agreement.email_account || '').toLowerCase().includes(lowerCaseSearchTerm) ||
                (agreement.your_name || '').toLowerCase().includes(lowerCaseSearchTerm) ||
                (agreement.father_name || '').toLowerCase().includes(lowerCaseSearchTerm)
        );

        const sorted = [...filtered].sort((a, b) => {
            const timeA = a.submitted ? a.submitted.getTime() : 0;
            const timeB = b.submitted ? b.submitted.getTime() : 0;
            if (sortOption === 'Newest') {
                return timeB - timeA;
            } else if (sortOption === 'Oldest') {
                return timeA - timeB;
            }
            return 0;
        });

        const byStatus = statusFilter ? sorted.filter((ag) => ag.status === statusFilter) : sorted;
        setFilteredAgreements(byStatus);
    }, [agreements, agreementSearchTerm, sortOption, statusFilter]);

    useEffect(() => {
        const lowerCaseSearchTerm = userSearchTerm.toLowerCase();
        const filtered = users.filter(
            (user) =>
                (user.phone_number || '').toLowerCase().includes(lowerCaseSearchTerm) ||
                (user.email || '').toLowerCase().includes(lowerCaseSearchTerm) ||
                (user.username || '').toLowerCase().includes(lowerCaseSearchTerm)
        );
        setFilteredUsers(filtered);
    }, [users, userSearchTerm]);

    useEffect(() => {
        if (id) {
            fetchAgreementDetail(id);
        }
    }, [id]);

    // --- Audit trail ---
    const fetchAuditLogs = async () => {
        setAuditLoading(true);
        try {
            const res = await api.get(API_ENDPOINTS.AUDIT_LOG);
            const entries = Array.isArray(res.data) ? res.data : res.data?.results || [];
            setAuditLogs(entries);
        } catch (err) {
            console.error('Failed to fetch audit logs:', err);
            setAuditLogs([]);
        } finally {
            setAuditLoading(false);
        }
    };

    const handleDownloadPdf = async (agreementId, name) => {
        try {
            const filename = `agreement_${agreementId}_${(name || 'summary').replace(/\s+/g, '_')}.pdf`;
            await downloadAuthedFile(`api/agreement/${agreementId}/pdf/`, filename);
        } catch (err) {
            console.error('PDF download failed:', err);
            setError('Failed to download the agreement PDF. Please try again.');
        }
    };

    useEffect(() => {
        if (activeTab === 'audit') {
            fetchAuditLogs();
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [activeTab]);

    // --- Render Functions ---

    const renderAgreementDetail = () => {
        if (loadingDetail) {
            return <div className="loading">Loading agreement details...</div>;
        }
        if (errorDetail) {
            return <div className="error-message">{errorDetail}</div>;
        }
        if (!agreement) {
            return <div className="not-found">Agreement not found.</div>;
        }

        // Construct full image URLs using the API base URL
        const getImageUrl = (path) => {
            if (!path) return null;
            // If path is already a full URL, return it; otherwise, prepend the API base URL
            return path.startsWith('http') ? path : `${api.defaults.baseURL}${path}`;
        };

        // Add Authorization header to image requests if needed
        const imgProps = {
            onError: (e) => {
                console.error('Image failed to load:', e.target.src);
                e.target.src = ''; // Fallback to empty string to avoid broken image icon
                e.target.alt = 'Image failed to load';
            },
            style: { maxWidth: '100%', maxHeight: '200px' }, // Optional: ensure images fit within the box
        };

        return (
            <div className="agreement-detail-content">
                <div className="detail-grid">
                    <div className="info-column">
                        <div className="agreement-form-section">
                            <h2>Personal Information</h2>
                            <div className="info-group">
                                <strong>Name</strong>
                                <span>{agreement.your_name || 'N/A'}</span>
                            </div>
                            <div className="info-group">
                                <strong>Father Name</strong>
                                <span>{agreement.father_name || 'N/A'}</span>
                            </div>
                            <div className="info-group">
                                <strong>Grand Father Name</strong>
                                <span>{agreement.grand_father_name || 'N/A'}</span>
                            </div>
                            <div className="info-group">
                                <strong>Gender</strong>
                                <span>{agreement.gender || 'N/A'}</span>
                            </div>
                            <div className="info-group">
                                <strong>User ID</strong>
                                <span>{agreement.id || 'N/A'}</span>
                            </div>
                            <div className="info-group">
                                <strong>Joined Date</strong>
                                <span>{agreement.submited_date ? new Date(agreement.submited_date).toLocaleDateString() : 'N/A'}</span>
                            </div>
                        </div>
                        <div className="agreement-form-section">
                            <h2>Address</h2>
                            <div className="info-group">
                                <strong>Country</strong>
                                <span>{agreement.nationality || 'N/A'}</span>
                            </div>
                            <div className="info-group">
                                <strong>City/Town</strong>
                                <span>{agreement.city || 'N/A'}</span>
                            </div>
                            <div className="info-group">
                                <strong>Werda/kebel</strong>
                                <span>{agreement.address || 'N/A'}</span>
                            </div>
                        </div>
                        <div className="agreement-form-section">
                            <h2>Contact Information</h2>
                            <div className="info-group">
                                <strong>Phone Number</strong>
                                <span>{agreement.phone_number || 'N/A'}</span>
                            </div>
                            <div className="info-group">
                                <strong>Email account</strong>
                                <span>{agreement.email_account || 'N/A'}</span>
                            </div>
                        </div>
                        <div className="agreement-form-section">
                            <h2>Signed Paper</h2>
                            <div className="info-group">
                                <strong>Agreement paper</strong>
                                <span>{agreement.pdf_agreement_name || 'N/A'}</span>
                            </div>
                            <div className="info-group">
                                <strong>Status</strong>
                                <span className={`status-badge status-${agreement.status}`}>{(agreement.status_display || agreement.status || 'N/A').toUpperCase()}</span>
                            </div>
                        </div>
                    </div>
                    <div className="signature-column">
                        <div><strong>Signature</strong></div>
                        <div className="signature-box">
                            {agreement.signature ? (
                                <img
                                    src={getImageUrl(agreement.signature)}
                                    alt="User Signature"
                                    {...imgProps}
                                />
                            ) : (
                                <span>No signature available</span>
                            )}
                        </div> 
                        <div><strong>Profile Photo</strong></div>
                        <div className="signature-box">
                            {agreement.profile_photo ? (
                                <img
                                    src={getImageUrl(agreement.profile_photo)}
                                    alt="User profile photo"
                                    {...imgProps}
                                />
                            ) : (
                                <span>No profile photo available</span>
                            )}
                        </div> 
                        <div><strong>Photo of ID</strong></div>
                        <div className="signature-box">
                            {agreement.photo_of_userID ? (
                                <img
                                    src={getImageUrl(agreement.photo_of_userID)}
                                    alt="User photo of ID"
                                    {...imgProps}
                                />
                            ) : (
                                <span>No photo of ID available</span>
                            )}
                        </div>
                    </div>
                </div>
                <div className="detail-actions">
                    <button
                        className="btn-primary"
                        onClick={() => handleDownloadPdf(agreement.id, agreement.your_name)}
                    >
                        <FaDownload /> Download Summary PDF
                    </button>
                    <button className="back-btn" onClick={() => navigate(-1)}>Back</button>
                </div>
            </div>
        );
    };

    const renderUploadForm = () => (
        <div className="upload-container">
            <h2>{pdfEditingId ? 'Edit PDF Agreement' : 'Upload New PDF Agreement'}</h2>
            <form onSubmit={handlePdfUpload}>
                <div className="form-group">
                    <label htmlFor="title">Agreement Title</label>
                    <input
                        type="text"
                        id="title"
                        value={pdfAgreementTitle}
                        onChange={handlePdfTitleChange}
                        placeholder="e.g., Non-Disclosure Agreement"
                        required
                    />
                </div>
                <div className="form-group">
                    <label htmlFor="pdf-file">PDF File</label>
                    <input
                        type="file"
                        id="pdf-file"
                        accept="application/pdf"
                        onChange={handlePdfFileChange}
                        required={!pdfEditingId}
                    />
                </div>
                <div className="button-group">
                    <button type="submit" className="btn-primary">{pdfEditingId ? 'Save Changes' : 'Upload'}</button>
                    <button type="button" className="btn-secondary" onClick={handleGoBack}>Cancel</button>
                </div>
            </form>
        </div>
    );

    const renderPdfAgreementList = () => (
        <div className="list-container">
            <div className="list-header">
                <h2>PDF Agreement Titles</h2>
                {isAdmin && (
                    <div className="admin-actions">
                        <button
                            className="btn-primary"
                            onClick={() => {
                                setActiveTab('pdf-upload');
                                setPdfAgreementTitle('');
                                setPdfAgreementFile(null);
                                setPdfEditingId(null);
                            }}
                        >
                            <FaPlus /> Add New
                        </button>
                    </div>
                )}
            </div>
            {pdfLoading ? (
                <p>Loading PDF agreements...</p>
            ) : pdfError ? (
                <p style={{ color: 'red' }}>{pdfError}</p>
            ) : pdfAgreements.length > 0 ? (
                <ul className="agreement-list">
                    {pdfAgreements.map((agreement) => (
                        <li 
                            key={agreement.id} 
                            className="agreement-item"
                            onClick={() => handleViewPdf(agreement.pdf_url)}
                        >
                            <span className="agreement-title">{agreement.type_of_agreement}</span>
                            <div className="actions">
                                {isAdmin && (
                                    <>
                                        <button className="btn-edit" onClick={(e) => { e.stopPropagation(); handlePdfEdit(agreement.id); }}>
                                            <FaEdit /> Edit
                                        </button>
                                        <button className="btn-delete" onClick={(e) => { e.stopPropagation(); handlePdfDelete(agreement.id); }}>
                                            <FaTrashAlt /> Delete
                                        </button>
                                    </>
                                )}
                            </div>
                        </li>
                    ))}
                </ul>
            ) : (
                <p>No PDF agreements found. Add a new one to get started.</p>
            )}
        </div>
    );

    const renderAuditTrail = () => (
        <div className="audit-trail-table">
            <div className="agreements-header">
                <h2>Audit Trail</h2>
                <div className="table-controls">
                    <button className="btn-secondary" onClick={fetchAuditLogs}>
                        <FaHistory /> Refresh
                    </button>
                </div>
            </div>
            {auditLoading ? (
                <p>Loading audit trail...</p>
            ) : auditLogs.length === 0 ? (
                <p>No audit entries yet. Actions on agreements will appear here.</p>
            ) : (
                <table>
                    <thead>
                        <tr>
                            <th>Time</th>
                            <th>Action</th>
                            <th>Agreement</th>
                            <th>Actor</th>
                            <th>Details</th>
                        </tr>
                    </thead>
                    <tbody>
                        {auditLogs.map((entry) => (
                            <tr key={entry.id}>
                                <td data-label="Time">{new Date(entry.timestamp).toLocaleString()}</td>
                                <td data-label="Action">
                                    <span className={`audit-action audit-${entry.action}`}>{entry.action.replace('_', ' ')}</span>
                                </td>
                                <td className="text-truncate" data-label="Agreement">
                                    {entry.agreement_name || '—'}
                                    {entry.agreement_id ? ` (#${entry.agreement_id})` : ''}
                                </td>
                                <td data-label="Actor">{entry.actor || entry.actor_name || 'system'}</td>
                                <td className="text-truncate" data-label="Details">{entry.details || '—'}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            )}
        </div>
    );

    const renderAgreementsTable = () => (
        <div className="agreements-table">
            <div className="agreements-header">
                <div className="agreements-header-title">
                    <div className="agreements-subheader-info">
                        <h3>All Agreements</h3>
                    </div>
                </div>
                <div className="table-controls">
                    <div className="search-container">
                        <FaSearch className="search-icon" />
                        <input
                            type="text"
                            placeholder="Search by phone, email, name, or father's name"
                            value={agreementSearchTerm}
                            onChange={(e) => setAgreementSearchTerm(e.target.value)}
                            className="search-input"
                        />
                    </div>
                    <div className="sort-by-dropdown">
                        <span>Status:</span>
                        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
                            <option value="">All</option>
                            <option value="pending">Pending</option>
                            <option value="approved">Approved</option>
                            <option value="rejected">Rejected</option>
                        </select>
                        <span>Sort by:</span>
                        <select value={sortOption} onChange={handleSortChange}>
                            <option value="Newest">Newest</option>
                            <option value="Oldest">Oldest</option>
                        </select>
                    </div>
                </div>
            </div>
            {filteredAgreements.length === 0 ? (
                <p>No agreements found.</p>
            ) : (
                <table>
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Phone Number</th>
                            <th>Email</th>
                            <th>Gender</th>
                            <th>Status</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        {filteredAgreements.map((agreement) => (
                            <tr key={agreement.id}>
                                <td className="text-truncate" data-label="Name">{`${agreement.your_name || 'N/A'} ${agreement.father_name || ''}`.trim()}</td>
                                <td className="text-truncate" data-label="Phone_number">{agreement.phone_number || 'N/A'}</td>
                                <td className="text-truncate" data-label="Email">{agreement.email_account || 'N/A'}</td>
                                <td className="text-truncate" data-label="Gender">{agreement.gender || 'N/A'}</td>
                                <td className="text-truncate" data-label="Status">
                                    <select
                                        className={`status-dropdown status-${agreement.status.toLowerCase()}`}
                                        value={agreement.status.toLowerCase()}
                                        onChange={(e) => handleStatusChange(agreement.id, e.target.value)}
                                    >
                                        <option value="approved">Approved</option>
                                        <option value="rejected">Rejected</option>
                                        <option value="pending">Pending</option>
                                    </select>
                                </td>
                                <td data-label="Action">
                                    <button onClick={() => navigate(`/agreements/${agreement.id}`)} className="view-btn">
                                        View
                                    </button>
                                    <button
                                        onClick={() => handleDownloadPdf(agreement.id, agreement.your_name)}
                                        className="view-btn"
                                        title="Download summary PDF"
                                    >
                                        <FaDownload />
                                    </button>
                                    <button onClick={() => handleDeleteAgreement(agreement.id)} className="delete-btn">
                                        Delete
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            )}
        </div>
    );

    const renderUsersTable = () => (
        <div className="users-table">
            <div className="agreements-header">
                <h2>User Management</h2>
                <div className="table-controls">
                    <div className="search-container">
                        <FaSearch className="search-icon" />
                        <input
                            type="text"
                            placeholder="Search by username, phone or email"
                            value={userSearchTerm}
                            onChange={(e) => setUserSearchTerm(e.target.value)}
                            className="search-input"
                        />
                    </div>
                </div>
            </div>
            {filteredUsers.length === 0 ? (
                <p>No users found.</p>
            ) : (
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Username</th>
                            <th>Email</th>
                            <th>Phone Number</th>
                            <th>Created At</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        {filteredUsers.map((user) => (
                            <tr key={user.id}>
                                <td data-label="ID">{user.id}</td>
                                <td className="text-truncate" data-label="Username">{user.username}</td>
                                <td className="text-truncate" data-label="Email">{user.email || 'N/A'}</td>
                                <td className="text-truncate" data-label="Phone Number">{user.phone_number || 'N/A'}</td>
                                <td className="text-truncate" data-label="Created At">
                                    {user.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}
                                </td>
                                <td>
                                    <button onClick={() => handleDeleteUser(user.id)} className="delete-btn">
                                        Delete
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            )}
        </div>
    );
    
    if (loading) {
        return <div className="admin-loading">Loading dashboard...</div>;
    }

    const navLinks = (
        <>
            <div
                className={`nav-item ${activeTab === 'agreements' ? 'active' : ''}`}
                onClick={() => handleTabClick('agreements')}
            >
                <FaChartBar className="nav-icon" /> Agreements
            </div>
            <div
                className={`nav-item ${activeTab === 'users' ? 'active' : ''}`}
                onClick={() => handleTabClick('users')}
            >
                <FaUsers className="nav-icon" /> Users
            </div>
            <div
                className={`nav-item ${activeTab === 'pdf-agreements' || activeTab === 'pdf-upload' ? 'active' : ''}`}
                onClick={() => handleTabClick('pdf-agreements')}
            >
                <FaFilePdf className="nav-icon" /> PDF Agreements
            </div>
            <div
                className={`nav-item ${activeTab === 'audit' ? 'active' : ''}`}
                onClick={() => handleTabClick('audit')}
            >
                <FaHistory className="nav-icon" /> Audit Trail
            </div>
            <div className="nav-item" onClick={handleLogout}>
                <FaSignOutAlt className="nav-icon" /> Log Out
            </div>
        </>
    );

    return (
        <div className="admin-dashboard-layout">
            {isConfirmModalOpen && <CustomConfirm message={confirmMessage} onConfirm={handleConfirm} onCancel={handleCancel} />}
            {isSidebarOpen && <div className="backdrop" onClick={() => setIsSidebarOpen(false)}></div>}

            <button className="hamburger-menu-btn" onClick={() => setIsSidebarOpen(true)}>
                <FaBars />
            </button>

            <nav className="admin-main-nav">
                <div className="admin-nav-header">
                    <div className="logo-main">Ashewa</div>
                    <div className="logo-sub">Cloud Business Trading S.C.</div>
                </div>
                <div className="admin-nav-links">
                    {navLinks}
                </div>
            </nav>

            <aside className={`mobile-sidebar ${isSidebarOpen ? 'open' : ''}`}>
                <div className="sidebar-logo">
                    <div className="logo-main">Ashewa</div>
                    <div className="logo-sub">Cloud Enterprise and Technology</div>
                </div>
                <div className="mobile-sidebar-header">
                    <button className="close-menu-btn" onClick={() => setIsSidebarOpen(false)}>
                        <FaTimes />
                    </button>
                </div>
                <div className="sidebar-section">
                    <div className="sidebar-section-title">MENU</div>
                    <nav className="mobile-sidebar-nav">
                        {navLinks}
                    </nav>
                </div>
            </aside>

            <main className="main-content">
                <header className="admin-header">
                    <h1>
                        {{
                            agreements: 'Agreement Management',
                            users: 'User Management',
                            'pdf-agreements': 'PDF Agreements',
                            'pdf-upload': 'Upload PDF Agreement',
                            audit: 'Audit Trail',
                        }[activeTab] || 'Agreement Management'}
                    </h1>
                </header>
                {error && (
                    <div className="error-message">
                        {error.split('\n').map((line, i) => (
                            <div key={i}>{line}</div>
                        ))}
                    </div>
                )}
                <div className="admin-content-card">
                    {id ? (
                        renderAgreementDetail()
                    ) : (
                        <>
                            {activeTab === 'agreements' && renderAgreementsTable()}
                            {activeTab === 'users' && renderUsersTable()}
                            {activeTab === 'pdf-agreements' && renderPdfAgreementList()}
                            {activeTab === 'pdf-upload' && renderUploadForm()}
                            {activeTab === 'audit' && renderAuditTrail()}

                            <div className="pagination">
                                <span>
                                    Showing {filteredAgreements.length} agreement{filteredAgreements.length === 1 ? '' : 's'}
                                </span>
                            </div>
                        </>
                    )}
                </div>
            </main>
            {isPdfViewerOpen && (
                <PdfViewer pdfUrl={currentPdfUrl} onClose={() => setIsPdfViewerOpen(false)} />
            )}
        </div>
    );
};

export default AdminDashboard;