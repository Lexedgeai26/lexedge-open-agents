
import React from 'react';

// --- Shared Styles ---
const cardStyle = {
    borderLeft: '3px solid',
    padding: '8px 10px',
    margin: '2px 0',
    borderRadius: '8px',
    background: '#ffffff',
    boxShadow: '0 1px 2px rgba(0,0,0,0.05)'
};

const badgeStyle = {
    color: 'white',
    padding: '2px 8px',
    borderRadius: '999px',
    fontSize: '0.7rem',
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: '0.04em',
    display: 'inline-block'
};

const sectionTitleStyle = {
    display: 'block',
    marginBottom: '2px',
    fontSize: '0.78rem',
    fontWeight: '600'
};

const listStyle = {
    margin: '0',
    paddingLeft: '12px',
    fontSize: '0.8rem',
    lineHeight: '1.35'
};

const disclaimerStyle = {
    fontSize: '0.68rem',
    color: '#94a3b8',
    margin: '4px 0 0',
    fontStyle: 'italic'
};

// --- Helper for Risk Colors ---
const getRiskColor = (risk) => {
    const r = (risk || 'low').toLowerCase();
    if (r === 'emergency') return '#ef4444';
    if (r === 'high') return '#f97316';
    if (r === 'moderate') return '#eab308';
    return '#22c55e'; // low or default
};

// --- 1. Assessment Card ---
export const AssessmentCard = ({ data }) => {
    const risk = data.risk_signal || 'low';
    const color = getRiskColor(risk);

    return (
        <div style={{ ...cardStyle, borderLeftColor: color }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                <span style={{ ...badgeStyle, background: color }}>
                    {risk} Risk Signal
                </span>
            </div>

            {data.suspected_patterns && data.suspected_patterns.length > 0 && (
                <div style={{ marginBottom: '4px' }}>
                    <strong style={{ ...sectionTitleStyle, color: '#1e293b' }}>🧬 Suspected Patterns</strong>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                        {data.suspected_patterns.map((p, i) => (
                            <span key={i} style={{ background: '#f8fafc', border: '1px solid #e2e8f0', padding: '1px 6px', borderRadius: '4px', fontSize: '0.78rem' }}>
                                {p}
                            </span>
                        ))}
                    </div>
                </div>
            )}

            {data.red_flags && data.red_flags.length > 0 && (
                <div style={{ background: '#fef2f2', border: '1px solid #fee2e2', borderRadius: '6px', padding: '6px 8px', marginBottom: '4px' }}>
                    <strong style={{ ...sectionTitleStyle, color: '#991b1b' }}>🚨 Red Flags Detected</strong>
                    <ul style={{ ...listStyle, color: '#b91c1c' }}>
                        {data.red_flags.map((flag, i) => <li key={i}>{flag}</li>)}
                    </ul>
                </div>
            )}

            {data.clinical_findings && data.clinical_findings.length > 0 && (
                <div style={{ marginBottom: '4px' }}>
                    <strong style={{ ...sectionTitleStyle, color: '#1e293b' }}>📊 Clinical Findings</strong>
                    <ul style={listStyle}>
                        {data.clinical_findings.map((item, i) => <li key={i}>{item}</li>)}
                    </ul>
                </div>
            )}

            {data.missing_details && data.missing_details.length > 0 && (
                <div style={{ background: '#f0f9ff', border: '1px solid #e0f2fe', borderRadius: '6px', padding: '6px 8px', marginBottom: '4px' }}>
                    <strong style={{ ...sectionTitleStyle, color: '#0369a1' }}>❓ Missing Information</strong>
                    <ul style={{ ...listStyle, color: '#075985' }}>
                        {data.missing_details.map((m, i) => <li key={i}>{m}</li>)}
                    </ul>
                </div>
            )}

            {data.recommended_follow_up && (
                <div style={{ marginTop: '4px', borderTop: '1px dashed #e2e8f0', paddingTop: '4px' }}>
                    <strong style={{ ...sectionTitleStyle, color: '#4f46e5' }}>🎯 Recommended Follow-up</strong>
                    <p style={{ color: '#4338ca', fontSize: '0.88rem', fontWeight: '600', margin: '0', lineHeight: '1.35' }}>
                        {data.recommended_follow_up}
                    </p>
                </div>
            )}

            <p style={disclaimerStyle}>Disclaimer: AI-assisted insight. Consult a physician.</p>
        </div>
    );
};

// --- 2. Diagnosis Card ---
export const DiagnosisCard = ({ data }) => {
    const color = '#8b5cf6'; // Purple

    return (
        <div style={{ ...cardStyle, borderLeftColor: color }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                <span style={{ ...badgeStyle, background: color }}>
                    🔬 Potential Diagnosis
                </span>
            </div>

            {data.conditions && (
                <div style={{ marginBottom: '8px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    {data.conditions.map((cond, i) => {
                        const name = typeof cond === 'string' ? cond : cond.name;
                        const prob = typeof cond === 'string' ? '' : cond.probability;
                        return (
                            <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#f5f3ff', padding: '6px 8px', borderRadius: '6px' }}>
                                <span style={{ color: '#4c1d95', fontWeight: '600', fontSize: '0.85rem' }}>{name}</span>
                                {prob && <span style={{ fontSize: '0.7rem', color: '#64748b', background: '#f1f5f9', padding: '1px 6px', borderRadius: '4px' }}>{prob}</span>}
                            </div>
                        );
                    })}
                </div>
            )}

            {data.reasoning && (
                <div style={{ marginBottom: '8px' }}>
                    <p style={{ color: '#4b5563', fontSize: '0.8rem', lineHeight: '1.4', margin: '0' }}>{data.reasoning}</p>
                </div>
            )}

            {data.treatment_plan && data.treatment_plan.length > 0 && (
                <div style={{ marginTop: '6px', borderTop: '1px dashed #e2e8f0', paddingTop: '6px' }}>
                    <strong style={{ ...sectionTitleStyle, color: '#4b5563' }}>📋 Suggested Approach</strong>
                    <ul style={{ ...listStyle, color: '#334155' }}>
                        {data.treatment_plan.map((item, i) => <li key={i}>{item}</li>)}
                    </ul>
                </div>
            )}

            <p style={disclaimerStyle}>Disclaimer: Consult a specialist for confirmation.</p>
        </div>
    );
};

// --- 3. Media Card ---
export const MediaCard = ({ data }) => {
    const severity = (data.severity || 'routine').toLowerCase();
    const severityColors = { "emergency": "#ef4444", "urgent": "#f97316", "routine": "#22c55e", "normal": "#22c55e" };
    const color = severityColors[severity] || '#64748b';
    const modality = (data.modality || 'Imaging').toUpperCase();

    return (
        <div style={{ ...cardStyle, borderLeftColor: color, background: '#f8fafc' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <span style={{ ...badgeStyle, background: color }}>
                    📷 {modality} Analysis
                </span>
                {data.confidence_score && (
                    <span style={{ fontSize: '0.65rem', color: '#64748b', fontWeight: 'bold' }}>
                        Confidence: {data.confidence_score}
                    </span>
                )}
            </div>

            {data.impression && (
                <div style={{ marginBottom: '10px', background: '#ffffff', padding: '10px', borderRadius: '8px', border: '1px solid #e2e8f0', boxShadow: '0 1px 2px rgba(0,0,0,0.02)' }}>
                    <strong style={{ display: 'block', color: '#1e293b', fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.025em', marginBottom: '4px' }}>
                        Clinical Impression
                    </strong>
                    <p style={{ margin: '0', color: '#0f172a', fontSize: '0.9rem', fontWeight: '600', lineHeight: '1.4' }}>{data.impression}</p>
                </div>
            )}

            <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '8px', marginBottom: '10px' }}>
                {data.findings && data.findings.length > 0 && (
                    <div style={{ background: 'white', padding: '8px', borderRadius: '6px', border: '1px solid #f1f5f9' }}>
                        <strong style={{ ...sectionTitleStyle, color: '#475569', fontSize: '0.7rem' }}>KEY OBSERVATIONS</strong>
                        <ul style={{ ...listStyle, color: '#334155', marginTop: '4px' }}>
                            {data.findings.map((f, i) => <li key={i}>{f}</li>)}
                        </ul>
                    </div>
                )}

                {data.technical_observations && (
                    <div style={{ background: '#f1f5f9', padding: '8px', borderRadius: '6px' }}>
                        <strong style={{ ...sectionTitleStyle, color: '#475569', fontSize: '0.7rem' }}>TECHNICAL CLINICAL DATA</strong>
                        <p style={{ margin: '4px 0 0 0', color: '#334155', fontSize: '0.78rem', lineHeight: '1.5', whiteSpace: 'pre-line' }}>{data.technical_observations}</p>
                    </div>
                )}
            </div>

            {data.abnormalities && data.abnormalities.length > 0 && (
                <div style={{ background: '#fef2f2', border: '1px solid #fee2e2', borderRadius: '6px', padding: '8px', marginBottom: '8px' }}>
                    <strong style={{ ...sectionTitleStyle, color: '#b91c1c', fontSize: '0.7rem' }}>Abnormalities Detected</strong>
                    <ul style={{ ...listStyle, color: '#991b1b', marginTop: '4px' }}>
                        {data.abnormalities.map((a, i) => <li key={i}>{a}</li>)}
                    </ul>
                </div>
            )}

            {data.recommendation && (
                <div style={{ marginTop: '8px', borderTop: '1px dashed #cbd5e1', paddingTop: '8px' }}>
                    <strong style={{ ...sectionTitleStyle, color: '#4f46e5', fontSize: '0.7rem' }}>CLINICAL RECOMMENDATION</strong>
                    <p style={{ margin: '4px 0 0 0', color: '#4338ca', fontSize: '0.82rem', fontWeight: '500' }}>{data.recommendation}</p>
                </div>
            )}

            <p style={{ ...disclaimerStyle, textAlign: 'center', marginTop: '10px' }}>
                Legal Document Record - LexEdge AI
            </p>
        </div>
    );
};

// --- 3a. Lab Report Card (Enhanced with tables and reference ranges) ---
export const LabReportCard = ({ data }) => {
    const severity = (data.severity || 'routine').toLowerCase();
    const severityColors = { "emergency": "#ef4444", "urgent": "#f97316", "routine": "#22c55e", "normal": "#22c55e" };
    const color = severityColors[severity] || '#3b82f6';

    // Group lab values by category
    const labValues = data.lab_values || [];
    const groupedValues = labValues.reduce((acc, item) => {
        const category = item.category || 'Other';
        if (!acc[category]) acc[category] = [];
        acc[category].push(item);
        return acc;
    }, {});

    // Status color helper
    const getStatusColor = (status) => {
        const s = (status || '').toLowerCase();
        if (s === 'critical') return { bg: '#fef2f2', text: '#dc2626', border: '#fecaca' };
        if (s === 'high') return { bg: '#fff7ed', text: '#ea580c', border: '#fed7aa' };
        if (s === 'low') return { bg: '#eff6ff', text: '#2563eb', border: '#bfdbfe' };
        return { bg: '#f0fdf4', text: '#16a34a', border: '#bbf7d0' };
    };

    // Calculate percentage for visual bar
    const getBarPercentage = (value, min, max) => {
        if (min === undefined || max === undefined || value === undefined) return null;
        const numValue = parseFloat(value);
        const numMin = parseFloat(min);
        const numMax = parseFloat(max);
        if (isNaN(numValue) || isNaN(numMin) || isNaN(numMax)) return null;

        const range = numMax - numMin;
        const midpoint = numMin + range / 2;
        const extendedMin = numMin - range * 0.3;
        const extendedMax = numMax + range * 0.3;
        const extendedRange = extendedMax - extendedMin;

        return Math.max(0, Math.min(100, ((numValue - extendedMin) / extendedRange) * 100));
    };

    return (
        <div style={{ ...cardStyle, borderLeftColor: color, background: '#fafbfc' }}>
            {/* Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                <span style={{ ...badgeStyle, background: '#059669' }}>
                    🧪 Laboratory Report
                </span>
                <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                    {data.report_date && (
                        <span style={{ fontSize: '0.7rem', color: '#64748b' }}>
                            📅 {data.report_date}
                        </span>
                    )}
                    {data.confidence_score && (
                        <span style={{ fontSize: '0.65rem', color: '#64748b', fontWeight: 'bold' }}>
                            Confidence: {data.confidence_score}
                        </span>
                    )}
                </div>
            </div>

            {/* Clinical Impression */}
            {data.impression && (
                <div style={{ marginBottom: '12px', background: '#ffffff', padding: '12px', borderRadius: '8px', border: '1px solid #e2e8f0', boxShadow: '0 1px 3px rgba(0,0,0,0.04)' }}>
                    <strong style={{ display: 'block', color: '#0f172a', fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.025em', marginBottom: '4px' }}>
                        🔬 Clinical Impression
                    </strong>
                    <p style={{ margin: '0', color: '#1e293b', fontSize: '0.95rem', fontWeight: '600', lineHeight: '1.4' }}>{data.impression}</p>
                </div>
            )}

            {/* Lab Values Table */}
            {Object.keys(groupedValues).length > 0 && (
                <div style={{ marginBottom: '12px' }}>
                    <strong style={{ ...sectionTitleStyle, color: '#0f172a', fontSize: '0.8rem', marginBottom: '8px' }}>
                        📊 Test Results
                    </strong>

                    {Object.entries(groupedValues).map(([category, tests]) => (
                        <div key={category} style={{ marginBottom: '10px' }}>
                            <div style={{ background: '#f1f5f9', padding: '4px 8px', borderRadius: '4px', marginBottom: '6px' }}>
                                <strong style={{ fontSize: '0.72rem', color: '#475569', textTransform: 'uppercase' }}>{category}</strong>
                            </div>

                            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem' }}>
                                <thead>
                                    <tr style={{ background: '#f8fafc' }}>
                                        <th style={{ textAlign: 'left', padding: '6px 8px', borderBottom: '1px solid #e2e8f0', color: '#64748b', fontWeight: '600', fontSize: '0.7rem' }}>Test</th>
                                        <th style={{ textAlign: 'center', padding: '6px 8px', borderBottom: '1px solid #e2e8f0', color: '#64748b', fontWeight: '600', fontSize: '0.7rem' }}>Result</th>
                                        <th style={{ textAlign: 'center', padding: '6px 8px', borderBottom: '1px solid #e2e8f0', color: '#64748b', fontWeight: '600', fontSize: '0.7rem' }}>Reference</th>
                                        <th style={{ textAlign: 'center', padding: '6px 8px', borderBottom: '1px solid #e2e8f0', color: '#64748b', fontWeight: '600', fontSize: '0.7rem', width: '80px' }}>Status</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {tests.map((test, idx) => {
                                        const statusColors = getStatusColor(test.status);
                                        const barPercent = getBarPercentage(test.value, test.reference_min, test.reference_max);

                                        return (
                                            <tr key={idx} style={{ background: idx % 2 === 0 ? '#ffffff' : '#fafbfc' }}>
                                                <td style={{ padding: '8px', borderBottom: '1px solid #f1f5f9', color: '#334155', fontWeight: '500' }}>
                                                    {test.test_name}
                                                </td>
                                                <td style={{ padding: '8px', borderBottom: '1px solid #f1f5f9', textAlign: 'center' }}>
                                                    <span style={{
                                                        fontWeight: '700',
                                                        color: statusColors.text,
                                                        fontSize: '0.85rem'
                                                    }}>
                                                        {test.value}
                                                    </span>
                                                    {test.unit && <span style={{ color: '#94a3b8', fontSize: '0.7rem', marginLeft: '3px' }}>{test.unit}</span>}
                                                </td>
                                                <td style={{ padding: '8px', borderBottom: '1px solid #f1f5f9', textAlign: 'center', color: '#64748b', fontSize: '0.75rem' }}>
                                                    {test.reference_min !== undefined && test.reference_max !== undefined
                                                        ? `${test.reference_min} - ${test.reference_max}`
                                                        : '-'}
                                                </td>
                                                <td style={{ padding: '8px', borderBottom: '1px solid #f1f5f9', textAlign: 'center' }}>
                                                    <span style={{
                                                        display: 'inline-block',
                                                        padding: '2px 8px',
                                                        borderRadius: '4px',
                                                        fontSize: '0.65rem',
                                                        fontWeight: '600',
                                                        textTransform: 'uppercase',
                                                        background: statusColors.bg,
                                                        color: statusColors.text,
                                                        border: `1px solid ${statusColors.border}`
                                                    }}>
                                                        {test.status || 'N/A'}
                                                    </span>
                                                </td>
                                            </tr>
                                        );
                                    })}
                                </tbody>
                            </table>
                        </div>
                    ))}
                </div>
            )}

            {/* Visual Range Indicators (for key abnormal values) */}
            {labValues.filter(v => v.status && v.status.toLowerCase() !== 'normal').length > 0 && (
                <div style={{ marginBottom: '12px', background: '#fff', padding: '10px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                    <strong style={{ ...sectionTitleStyle, color: '#475569', fontSize: '0.7rem', marginBottom: '8px' }}>
                        📈 Abnormal Values - Visual Range
                    </strong>
                    {labValues.filter(v => v.status && v.status.toLowerCase() !== 'normal').slice(0, 5).map((test, idx) => {
                        const statusColors = getStatusColor(test.status);
                        const barPercent = getBarPercentage(test.value, test.reference_min, test.reference_max);
                        const normalStart = 23; // ~30% mark for normal range start
                        const normalEnd = 77;   // ~70% mark for normal range end

                        return (
                            <div key={idx} style={{ marginBottom: '8px' }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '2px' }}>
                                    <span style={{ fontSize: '0.75rem', color: '#334155', fontWeight: '500' }}>{test.test_name}</span>
                                    <span style={{ fontSize: '0.75rem', color: statusColors.text, fontWeight: '600' }}>
                                        {test.value} {test.unit}
                                    </span>
                                </div>
                                <div style={{ position: 'relative', height: '8px', background: '#f1f5f9', borderRadius: '4px', overflow: 'hidden' }}>
                                    {/* Normal range indicator */}
                                    <div style={{
                                        position: 'absolute',
                                        left: `${normalStart}%`,
                                        width: `${normalEnd - normalStart}%`,
                                        height: '100%',
                                        background: '#dcfce7',
                                        borderLeft: '2px solid #22c55e',
                                        borderRight: '2px solid #22c55e'
                                    }} />
                                    {/* Value marker */}
                                    {barPercent !== null && (
                                        <div style={{
                                            position: 'absolute',
                                            left: `${barPercent}%`,
                                            top: '-2px',
                                            width: '4px',
                                            height: '12px',
                                            background: statusColors.text,
                                            borderRadius: '2px',
                                            transform: 'translateX(-50%)'
                                        }} />
                                    )}
                                </div>
                                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.6rem', color: '#94a3b8', marginTop: '1px' }}>
                                    <span>Low</span>
                                    <span>Normal ({test.reference_min}-{test.reference_max})</span>
                                    <span>High</span>
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}

            {/* Findings (fallback if no structured lab_values) */}
            {data.findings && data.findings.length > 0 && labValues.length === 0 && (
                <div style={{ background: 'white', padding: '8px', borderRadius: '6px', border: '1px solid #f1f5f9', marginBottom: '10px' }}>
                    <strong style={{ ...sectionTitleStyle, color: '#475569', fontSize: '0.7rem' }}>KEY OBSERVATIONS</strong>
                    <ul style={{ ...listStyle, color: '#334155', marginTop: '4px' }}>
                        {data.findings.map((f, i) => <li key={i}>{f}</li>)}
                    </ul>
                </div>
            )}

            {/* Technical Observations */}
            {data.technical_observations && (
                <div style={{ background: '#f8fafc', padding: '10px', borderRadius: '6px', marginBottom: '10px', border: '1px solid #e2e8f0' }}>
                    <strong style={{ ...sectionTitleStyle, color: '#475569', fontSize: '0.7rem' }}>CLINICAL INTERPRETATION</strong>
                    <p style={{ margin: '4px 0 0 0', color: '#334155', fontSize: '0.8rem', lineHeight: '1.5', whiteSpace: 'pre-line' }}>{data.technical_observations}</p>
                </div>
            )}

            {/* Abnormalities */}
            {data.abnormalities && data.abnormalities.length > 0 && (
                <div style={{ background: '#fef2f2', border: '1px solid #fee2e2', borderRadius: '6px', padding: '8px', marginBottom: '10px' }}>
                    <strong style={{ ...sectionTitleStyle, color: '#b91c1c', fontSize: '0.7rem' }}>⚠️ Abnormalities Detected</strong>
                    <ul style={{ ...listStyle, color: '#991b1b', marginTop: '4px' }}>
                        {data.abnormalities.map((a, i) => <li key={i}>{a}</li>)}
                    </ul>
                </div>
            )}

            {/* Recommendation */}
            {data.recommendation && (
                <div style={{ marginTop: '8px', borderTop: '1px dashed #cbd5e1', paddingTop: '8px' }}>
                    <strong style={{ ...sectionTitleStyle, color: '#059669', fontSize: '0.7rem' }}>CLINICAL RECOMMENDATION</strong>
                    <p style={{ margin: '4px 0 0 0', color: '#047857', fontSize: '0.82rem', fontWeight: '500' }}>{data.recommendation}</p>
                </div>
            )}

            <p style={{ ...disclaimerStyle, textAlign: 'center', marginTop: '10px' }}>
                Legal Analysis Report - LexEdge AI
            </p>
        </div>
    );
};

// --- 3b. Radiology Card ---
export const RadiologyCard = ({ data }) => {
    const severity = (data.severity || 'routine').toLowerCase();
    const severityColors = { "critical": "#ef4444", "severe": "#ef4444", "moderate": "#f97316", "mild": "#eab308", "normal": "#22c55e" };
    const color = severityColors[severity] || '#3b82f6';
    const modality = (data.modality || 'Imaging').toUpperCase();

    return (
        <div style={{ ...cardStyle, borderLeftColor: color, background: '#f0f9ff' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <span style={{ ...badgeStyle, background: '#1e40af' }}>
                    🩻 {modality} Study
                </span>
                {data.confidence_score && (
                    <span style={{ fontSize: '0.65rem', color: '#64748b', fontWeight: 'bold' }}>
                        Confidence: {data.confidence_score}
                    </span>
                )}
            </div>

            {(data.body_region || data.technique) && (
                <div style={{ display: 'flex', gap: '8px', marginBottom: '8px', flexWrap: 'wrap' }}>
                    {data.body_region && (
                        <span style={{ background: '#dbeafe', color: '#1e40af', padding: '2px 8px', borderRadius: '4px', fontSize: '0.72rem', fontWeight: '500' }}>
                            📍 {data.body_region}
                        </span>
                    )}
                    {data.technique && (
                        <span style={{ background: '#e0e7ff', color: '#3730a3', padding: '2px 8px', borderRadius: '4px', fontSize: '0.72rem' }}>
                            {data.technique}
                        </span>
                    )}
                </div>
            )}

            {data.impression && (
                <div style={{ marginBottom: '10px', background: '#ffffff', padding: '10px', borderRadius: '8px', border: '1px solid #bfdbfe', boxShadow: '0 1px 2px rgba(0,0,0,0.02)' }}>
                    <strong style={{ display: 'block', color: '#1e40af', fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.025em', marginBottom: '4px' }}>
                        Radiological Impression
                    </strong>
                    <p style={{ margin: '0', color: '#0f172a', fontSize: '0.9rem', fontWeight: '600', lineHeight: '1.4' }}>{data.impression}</p>
                </div>
            )}

            <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '8px', marginBottom: '10px' }}>
                {data.findings && data.findings.length > 0 && (
                    <div style={{ background: 'white', padding: '8px', borderRadius: '6px', border: '1px solid #e0f2fe' }}>
                        <strong style={{ ...sectionTitleStyle, color: '#0369a1', fontSize: '0.7rem' }}>RADIOLOGICAL FINDINGS</strong>
                        <ul style={{ ...listStyle, color: '#334155', marginTop: '4px' }}>
                            {data.findings.map((f, i) => <li key={i}>{f}</li>)}
                        </ul>
                    </div>
                )}

                {data.technical_observations && (
                    <div style={{ background: '#f1f5f9', padding: '8px', borderRadius: '6px' }}>
                        <strong style={{ ...sectionTitleStyle, color: '#475569', fontSize: '0.7rem' }}>CLINICAL INTERPRETATION</strong>
                        <p style={{ margin: '4px 0 0 0', color: '#334155', fontSize: '0.78rem', lineHeight: '1.5', whiteSpace: 'pre-line' }}>{data.technical_observations}</p>
                    </div>
                )}
            </div>

            {data.abnormalities && data.abnormalities.length > 0 && (
                <div style={{ background: '#fef2f2', border: '1px solid #fee2e2', borderRadius: '6px', padding: '8px', marginBottom: '8px' }}>
                    <strong style={{ ...sectionTitleStyle, color: '#b91c1c', fontSize: '0.7rem' }}>⚠️ Abnormalities Identified</strong>
                    <ul style={{ ...listStyle, color: '#991b1b', marginTop: '4px' }}>
                        {data.abnormalities.map((a, i) => <li key={i}>{a}</li>)}
                    </ul>
                </div>
            )}

            {data.comparison && data.comparison !== "No prior studies available for comparison." && (
                <div style={{ background: '#fefce8', border: '1px solid #fef08a', borderRadius: '6px', padding: '8px', marginBottom: '8px' }}>
                    <strong style={{ ...sectionTitleStyle, color: '#a16207', fontSize: '0.7rem' }}>📊 Comparison with Prior Studies</strong>
                    <p style={{ margin: '4px 0 0 0', color: '#854d0e', fontSize: '0.78rem' }}>{data.comparison}</p>
                </div>
            )}

            {data.recommendation && (
                <div style={{ marginTop: '8px', borderTop: '1px dashed #93c5fd', paddingTop: '8px' }}>
                    <strong style={{ ...sectionTitleStyle, color: '#1e40af', fontSize: '0.7rem' }}>RADIOLOGIST RECOMMENDATION</strong>
                    <p style={{ margin: '4px 0 0 0', color: '#1e3a8a', fontSize: '0.82rem', fontWeight: '500' }}>{data.recommendation}</p>
                </div>
            )}

            <p style={{ ...disclaimerStyle, textAlign: 'center', marginTop: '10px' }}>
                Legal Document Report - LexEdge AI
            </p>
        </div>
    );
};

// --- 3c. Triage Card ---
export const TriageCard = ({ data }) => {
    const riskLevel = (data.risk_level || 'MEDIUM').toUpperCase();
    const riskColors = {
        "CRITICAL": "#dc2626",
        "HIGH": "#ea580c",
        "MEDIUM": "#eab308",
        "LOW": "#22c55e"
    };
    const color = riskColors[riskLevel] || '#64748b';
    const urgencyScore = data.urgency_score || 5;

    const getCategoryLabel = (category) => {
        const labels = {
            "EMERGENCY_REFERRAL": "🚨 Emergency Referral Required",
            "URGENT_CARE": "⚡ Urgent Care Needed",
            "ROUTINE_FOLLOWUP": "📅 Routine Follow-up",
            "HOME_CARE": "🏠 Home Care Appropriate",
            "SELF_MONITORING": "👁️ Self-Monitoring"
        };
        return labels[category] || category;
    };

    return (
        <div style={{ ...cardStyle, borderLeftColor: color, background: riskLevel === 'CRITICAL' ? '#fef2f2' : '#fefce8' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                <span style={{ ...badgeStyle, background: color, fontSize: '0.72rem' }}>
                    ⚠️ {riskLevel} RISK
                </span>
                <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <span style={{ fontSize: '0.65rem', color: '#64748b' }}>Urgency:</span>
                    <span style={{
                        fontSize: '0.8rem',
                        fontWeight: 'bold',
                        color: urgencyScore >= 7 ? '#dc2626' : urgencyScore >= 4 ? '#ea580c' : '#22c55e'
                    }}>
                        {urgencyScore}/10
                    </span>
                </div>
            </div>

            {data.triage_category && (
                <div style={{
                    background: riskLevel === 'CRITICAL' || riskLevel === 'HIGH' ? '#fee2e2' : '#fef9c3',
                    padding: '10px 12px',
                    borderRadius: '8px',
                    marginBottom: '10px',
                    border: `1px solid ${color}40`
                }}>
                    <strong style={{ fontSize: '0.95rem', color: '#0f172a' }}>
                        {getCategoryLabel(data.triage_category)}
                    </strong>
                    {data.timeframe && (
                        <p style={{ margin: '4px 0 0 0', fontSize: '0.8rem', color: '#475569' }}>
                            ⏱️ Timeframe: <strong>{data.timeframe}</strong>
                        </p>
                    )}
                </div>
            )}

            {data.red_flags && data.red_flags.length > 0 && (
                <div style={{ background: '#fef2f2', border: '1px solid #fee2e2', borderRadius: '6px', padding: '8px', marginBottom: '8px' }}>
                    <strong style={{ ...sectionTitleStyle, color: '#b91c1c', fontSize: '0.7rem' }}>🚨 RED FLAGS IDENTIFIED</strong>
                    <ul style={{ ...listStyle, color: '#991b1b', marginTop: '4px' }}>
                        {data.red_flags.map((flag, i) => <li key={i}>{flag}</li>)}
                    </ul>
                </div>
            )}

            {data.clinical_reasoning && (
                <div style={{ background: 'white', padding: '8px', borderRadius: '6px', border: '1px solid #e2e8f0', marginBottom: '8px' }}>
                    <strong style={{ ...sectionTitleStyle, color: '#475569', fontSize: '0.7rem' }}>CLINICAL REASONING</strong>
                    <p style={{ margin: '4px 0 0 0', color: '#334155', fontSize: '0.8rem', lineHeight: '1.5' }}>{data.clinical_reasoning}</p>
                </div>
            )}

            {data.contributing_factors && data.contributing_factors.length > 0 && (
                <div style={{ marginBottom: '8px' }}>
                    <strong style={{ ...sectionTitleStyle, color: '#475569', fontSize: '0.7rem' }}>CONTRIBUTING FACTORS</strong>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginTop: '4px' }}>
                        {data.contributing_factors.map((factor, i) => (
                            <span key={i} style={{ background: '#f1f5f9', padding: '2px 8px', borderRadius: '4px', fontSize: '0.72rem', color: '#475569' }}>
                                {factor}
                            </span>
                        ))}
                    </div>
                </div>
            )}

            {data.recommended_actions && data.recommended_actions.length > 0 && (
                <div style={{ background: '#f0fdf4', border: '1px solid #dcfce7', borderRadius: '6px', padding: '8px', marginBottom: '8px' }}>
                    <strong style={{ ...sectionTitleStyle, color: '#166534', fontSize: '0.7rem' }}>✅ RECOMMENDED ACTIONS</strong>
                    <ul style={{ ...listStyle, color: '#14532d', marginTop: '4px' }}>
                        {data.recommended_actions.map((action, i) => <li key={i}>{action}</li>)}
                    </ul>
                </div>
            )}

            {data.specialist_referral && (
                <div style={{ background: '#eff6ff', padding: '6px 8px', borderRadius: '6px', marginBottom: '8px' }}>
                    <strong style={{ fontSize: '0.72rem', color: '#1e40af' }}>👨‍⚕️ Specialist Referral: </strong>
                    <span style={{ fontSize: '0.8rem', color: '#1e3a8a' }}>{data.specialist_referral}</span>
                </div>
            )}

            {data.home_care_instructions && data.home_care_instructions.length > 0 && (
                <div style={{ background: '#fefce8', border: '1px solid #fef08a', borderRadius: '6px', padding: '8px', marginBottom: '8px' }}>
                    <strong style={{ ...sectionTitleStyle, color: '#a16207', fontSize: '0.7rem' }}>🏠 HOME CARE INSTRUCTIONS</strong>
                    <ul style={{ ...listStyle, color: '#854d0e', marginTop: '4px' }}>
                        {data.home_care_instructions.map((instr, i) => <li key={i}>{instr}</li>)}
                    </ul>
                </div>
            )}

            <p style={{ ...disclaimerStyle, textAlign: 'center', marginTop: '10px' }}>
                Risk Assessment - LexEdge AI | Always seek professional legal advice
            </p>
        </div>
    );
};

// --- 3d. Triage Final Report Card ---
export const TriageFinalReportCard = ({ data }) => {
    const riskLevel = (data.risk_level || 'MEDIUM').toUpperCase();
    const riskColors = {
        "CRITICAL": "#dc2626",
        "HIGH": "#ea580c",
        "MEDIUM": "#eab308",
        "LOW": "#22c55e"
    };
    const color = riskColors[riskLevel] || '#64748b';
    const urgencyScore = data.urgency_score || 5;

    const getCategoryLabel = (category) => {
        const labels = {
            "EMERGENCY_REFERRAL": "🚨 Emergency Referral Required",
            "URGENT_CARE": "⚡ Urgent Care Needed",
            "ROUTINE_FOLLOWUP": "📅 Routine Follow-up",
            "HOME_CARE": "🏠 Home Care Appropriate",
            "SELF_MONITORING": "👁️ Self-Monitoring"
        };
        return labels[category] || category;
    };

    return (
        <div style={{ ...cardStyle, borderLeftColor: color, background: '#fcfdfe', border: '1px solid #e0e7ff' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <span style={{ ...badgeStyle, background: '#1e293b' }}>
                    📋 Final Triage Report
                </span>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ ...badgeStyle, background: color, fontSize: '0.65rem' }}>
                        {riskLevel} RISK
                    </span>
                    <span style={{ fontSize: '0.7rem', color: '#64748b', background: '#f1f5f9', padding: '2px 8px', borderRadius: '4px', fontWeight: 'bold' }}>
                        Urgency: {urgencyScore}/10
                    </span>
                </div>
            </div>

            {data.triage_category && (
                <div style={{
                    background: riskLevel === 'CRITICAL' || riskLevel === 'HIGH' ? '#fee2e2' : '#fef9c3',
                    padding: '10px 12px',
                    borderRadius: '8px',
                    marginBottom: '12px',
                    border: `1px solid ${color}40`
                }}>
                    <strong style={{ fontSize: '0.95rem', color: '#0f172a' }}>
                        {getCategoryLabel(data.triage_category)}
                    </strong>
                    {data.timeframe && (
                        <p style={{ margin: '4px 0 0 0', fontSize: '0.8rem', color: '#475569' }}>
                            ⏱️ Timeframe: <strong>{data.timeframe}</strong>
                        </p>
                    )}
                </div>
            )}

            {data.interaction_summary && (
                <div style={{ marginBottom: '12px', padding: '10px', background: '#f8fafc', borderRadius: '8px', borderLeft: '3px solid #64748b' }}>
                    <strong style={{ ...sectionTitleStyle, color: '#475569', fontSize: '0.7rem' }}>SESSION SUMMARY</strong>
                    <p style={{ margin: '0', color: '#334155', fontSize: '0.82rem', lineHeight: '1.4' }}>{data.interaction_summary}</p>
                </div>
            )}

            <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '12px', marginBottom: '12px' }}>
                {data.clinical_presentation && (
                    <div style={{ background: 'white', padding: '10px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                        <strong style={{ ...sectionTitleStyle, color: '#0f172a' }}>🩺 Clinical Presentation</strong>
                        <p style={{ margin: '0', color: '#334155', fontSize: '0.85rem', lineHeight: '1.5' }}>{data.clinical_presentation}</p>
                    </div>
                )}

                {data.clinical_reasoning && (
                    <div style={{ background: '#f5f3ff', padding: '10px', borderRadius: '8px', border: '1px solid #ddd6fe' }}>
                        <strong style={{ ...sectionTitleStyle, color: '#4c1d95' }}>🧠 Clinical Reasoning</strong>
                        <p style={{ margin: '0', color: '#5b21b6', fontSize: '0.82rem', lineHeight: '1.5', whiteSpace: 'pre-line' }}>{data.clinical_reasoning}</p>
                    </div>
                )}
            </div>

            {data.red_flags_identified && data.red_flags_identified.length > 0 && (
                <div style={{ background: '#fef2f2', border: '1px solid #fee2e2', borderRadius: '6px', padding: '8px', marginBottom: '12px' }}>
                    <strong style={{ ...sectionTitleStyle, color: '#b91c1c', fontSize: '0.7rem' }}>🚨 RED FLAGS IDENTIFIED</strong>
                    <ul style={{ ...listStyle, color: '#991b1b', marginTop: '4px' }}>
                        {data.red_flags_identified.map((flag, i) => <li key={i}>{flag}</li>)}
                    </ul>
                </div>
            )}

            {data.definitive_recommendation && data.definitive_recommendation.length > 0 && (
                <div style={{ background: '#f0fdf4', padding: '12px', borderRadius: '8px', border: '1px solid #dcfce7', marginBottom: '10px' }}>
                    <strong style={{ ...sectionTitleStyle, color: '#166534' }}>📍 Definitive Recommendations</strong>
                    <ul style={{ ...listStyle, color: '#14532d', marginTop: '6px' }}>
                        {data.definitive_recommendation.map((step, i) => <li key={i} style={{ marginBottom: '4px' }}>{step}</li>)}
                    </ul>
                </div>
            )}

            {data.specialist_referral && (
                <div style={{ background: '#eff6ff', padding: '6px 8px', borderRadius: '6px', marginBottom: '8px' }}>
                    <strong style={{ fontSize: '0.72rem', color: '#1e40af' }}>👨‍⚕️ Specialist Referral: </strong>
                    <span style={{ fontSize: '0.8rem', color: '#1e3a8a' }}>{data.specialist_referral}</span>
                </div>
            )}

            {data.home_care_instructions && data.home_care_instructions.length > 0 && (
                <div style={{ background: '#fefce8', border: '1px solid #fef08a', borderRadius: '6px', padding: '8px', marginBottom: '8px' }}>
                    <strong style={{ ...sectionTitleStyle, color: '#a16207', fontSize: '0.7rem' }}>🏠 HOME CARE INSTRUCTIONS</strong>
                    <ul style={{ ...listStyle, color: '#854d0e', marginTop: '4px' }}>
                        {data.home_care_instructions.map((instr, i) => <li key={i}>{instr}</li>)}
                    </ul>
                </div>
            )}

            {data.return_precautions && data.return_precautions.length > 0 && (
                <div style={{ background: '#fef2f2', border: '1px solid #fecaca', borderRadius: '6px', padding: '8px', marginBottom: '8px' }}>
                    <strong style={{ ...sectionTitleStyle, color: '#991b1b', fontSize: '0.7rem' }}>⚠️ RETURN PRECAUTIONS - Seek Immediate Care If:</strong>
                    <ul style={{ ...listStyle, color: '#b91c1c', marginTop: '4px' }}>
                        {data.return_precautions.map((precaution, i) => <li key={i}>{precaution}</li>)}
                    </ul>
                </div>
            )}

            <p style={{ ...disclaimerStyle, marginTop: '12px', textAlign: 'center', borderTop: '1px solid #e2e8f0', paddingTop: '8px' }}>
                Legal Risk Record - LexEdge AI
            </p>
        </div>
    );
};

// --- 4. Educational Card ---
export const EducationalCard = ({ data }) => {
    const color = '#3b82f6'; // Blue
    const topic = data.topic || "Medical Information";
    const summary = data.explanation || data.summary || "";

    return (
        <div style={{ ...cardStyle, borderLeftColor: color }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                <span style={{ ...badgeStyle, background: color }}>
                    ℹ️ {topic}
                </span>
            </div>

            <div style={{ marginBottom: '6px' }}>
                <p style={{ color: '#334155', fontSize: '0.85rem', lineHeight: '1.4', margin: '0' }}>{summary}</p>
            </div>

            {data.key_points && data.key_points.length > 0 && (
                <div style={{ marginBottom: '6px' }}>
                    <strong style={{ ...sectionTitleStyle, color: '#1e293b' }}>📌 Key Points</strong>
                    <ul style={listStyle}>
                        {data.key_points.map((point, i) => <li key={i}>{point}</li>)}
                    </ul>
                </div>
            )}

            {data.related_topics && data.related_topics.length > 0 && (
                <div style={{ marginTop: '6px', borderTop: '1px dashed #cbd5e1', paddingTop: '4px' }}>
                    <strong style={{ color: '#64748b', fontSize: '0.75rem' }}>Related: </strong>
                    <span style={{ color: '#475569', fontSize: '0.75rem' }}>{data.related_topics.join(', ')}</span>
                </div>
            )}
            <p style={disclaimerStyle}>Disclaimer: For informational purposes only. Consult a physician.</p>
        </div>
    );
};

// --- 5. General Physician Card ---
export const GeneralPhysicianCard = ({ data }) => {
    const urgency = (data.urgency_level || 'Low').toLowerCase();
    const color = getRiskColor(urgency);

    return (
        <div style={{ ...cardStyle, borderLeftColor: color }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                <span style={{ ...badgeStyle, background: color }}>
                    👨‍⚕️ Physician Assessment
                </span>
                <span style={{ fontSize: '0.7rem', color: '#64748b', background: '#f1f5f9', padding: '2px 8px', borderRadius: '4px', fontWeight: 'bold' }}>
                    {data.urgency_level || 'Low'} Urgency
                </span>
            </div>

            {data.chief_complaint && (
                <div style={{ marginBottom: '8px' }}>
                    <strong style={{ ...sectionTitleStyle, color: '#1e293b' }}>Complaint</strong>
                    <p style={{ margin: '0', color: '#334155', fontSize: '0.85rem' }}>{data.chief_complaint}</p>
                </div>
            )}

            {data.symptom_analysis && (
                <div style={{ marginBottom: '8px' }}>
                    <strong style={{ ...sectionTitleStyle, color: '#1e293b' }}>Symptom Analysis</strong>
                    <p style={{ margin: '0', color: '#334155', fontSize: '0.85rem', whiteSpace: 'pre-line' }}>{data.symptom_analysis}</p>
                </div>
            )}

            {data.doctor_summary && (
                <div style={{ marginBottom: '8px', background: '#f8fafc', padding: '8px', borderRadius: '6px' }}>
                    <p style={{ margin: '0', color: '#1e293b', fontSize: '0.85rem', lineHeight: '1.4' }}>{data.doctor_summary}</p>
                </div>
            )}

            {data.possible_causes && data.possible_causes.length > 0 && (
                <div style={{ marginBottom: '8px' }}>
                    <strong style={{ ...sectionTitleStyle, color: '#1e293b' }}>Potential Causes</strong>
                    <ul style={listStyle}>
                        {data.possible_causes.map((cause, i) => <li key={i}>{cause}</li>)}
                    </ul>
                </div>
            )}

            {data.red_flags_to_check && data.red_flags_to_check.length > 0 && (
                <div style={{ background: '#fef2f2', border: '1px solid #fee2e2', borderRadius: '6px', padding: '8px', marginBottom: '8px' }}>
                    <strong style={{ ...sectionTitleStyle, color: '#991b1b' }}>🚨 Red Flags</strong>
                    <ul style={{ ...listStyle, color: '#b91c1c' }}>
                        {data.red_flags_to_check.map((flag, i) => <li key={i}>{flag}</li>)}
                    </ul>
                </div>
            )}

            {data.next_steps && data.next_steps.length > 0 && (
                <div style={{ marginTop: '8px', borderTop: '1px dashed #e2e8f0', paddingTop: '8px' }}>
                    <strong style={{ ...sectionTitleStyle, color: '#4f46e5' }}>📋 Recommended Next Steps</strong>
                    <ul style={{ ...listStyle, color: '#4338ca' }}>
                        {data.next_steps.map((step, i) => <li key={i}>{step}</li>)}
                    </ul>
                </div>
            )}

            <p style={disclaimerStyle}>Disclaimer: AI medical assessment. See a doctor immediately for emergencies.</p>
        </div>
    );
};

// --- 6. Smart Follow-up Card ---
export const SmartFollowupCard = ({ data, onSuggestionClick }) => {
    // Local state to track which options are selected for each question
    const [selections, setSelections] = React.useState({});

    const toggleOption = (qIdx, opt) => {
        setSelections(prev => {
            const currentQ = prev[qIdx] || [];
            if (currentQ.includes(opt)) {
                return { ...prev, [qIdx]: currentQ.filter(o => o !== opt) };
            } else {
                return { ...prev, [qIdx]: [...currentQ, opt] };
            }
        });
    };

    const handleSubmit = (isFinal = false) => {
        const answers = Object.entries(selections)
            .filter(([_, opts]) => opts.length > 0)
            .map(([qIdx, opts]) => {
                const question = data.questions[qIdx].question;
                return `Field: "${question}" | Findings: ${opts.join(', ')}`;
            });

        if (answers.length === 0 && !isFinal) return;

        let fullCommand = "";
        let caption = "";
        if (isFinal) {
            fullCommand = `[ACTION: CONCLUDE_ASSESSMENT] Please provide a final, definitive physician report based on all clinical findings shared so far: ${answers.join('; ')}.`;
            caption = "I'm ready for the final assessment.";
        } else {
            fullCommand = `[ACTION: UPDATE_RECORD] Patient clinical details: ${answers.join('; ')}`;
            caption = "I've added more details to the symptoms.";
        }

        onSuggestionClick({
            caption: caption,
            command: fullCommand
        });
    };

    const hasSelections = Object.values(selections).some(opts => opts.length > 0);

    return (
        <div style={{ ...cardStyle, borderLeftColor: '#3b82f6', background: '#f8fafc', border: '1px solid #e2e8f0', padding: '12px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <span style={{ ...badgeStyle, background: '#3b82f6', fontSize: '0.65rem' }}>
                    ⚡ CLINICAL DATA ENTRY
                </span>
            </div>

            <p style={{ fontSize: '0.78rem', color: '#64748b', marginBottom: '12px', fontStyle: 'italic' }}>
                Select relevant clinical observations to refine your assessment:
            </p>

            {data.questions && data.questions.map((q, qIdx) => (
                <div key={qIdx} style={{ marginBottom: '12px', background: 'white', padding: '8px', borderRadius: '6px', border: '1px solid #f1f5f9' }}>
                    <p style={{ fontSize: '0.82rem', fontWeight: '600', color: '#334155', margin: '0 0 8px 0', lineHeight: '1.3' }}>
                        {q.question}
                    </p>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                        {q.response_options && q.response_options.map((opt, oIdx) => {
                            const isSelected = (selections[qIdx] || []).includes(opt);
                            return (
                                <button
                                    key={oIdx}
                                    onClick={() => toggleOption(qIdx, opt)}
                                    style={{
                                        background: isSelected ? '#3b82f6' : '#ffffff',
                                        border: '1px solid',
                                        borderColor: isSelected ? '#2563eb' : '#e2e8f0',
                                        borderRadius: '6px',
                                        padding: '4px 10px',
                                        fontSize: '0.75rem',
                                        color: isSelected ? '#ffffff' : '#475569',
                                        cursor: 'pointer',
                                        transition: 'all 0.15s ease',
                                        fontWeight: isSelected ? '600' : '400',
                                        boxShadow: isSelected ? '0 2px 4px rgba(59, 130, 246, 0.2)' : 'none'
                                    }}
                                >
                                    {isSelected && <span style={{ marginRight: '4px' }}>✓</span>}
                                    {opt}
                                </button>
                            );
                        })}
                    </div>
                </div>
            ))}

            <div style={{ display: 'flex', gap: '8px', marginTop: '12px' }}>
                <button
                    onClick={() => handleSubmit(false)}
                    disabled={!hasSelections}
                    style={{
                        flex: 1,
                        padding: '10px',
                        background: hasSelections ? 'white' : '#f1f5f9',
                        color: hasSelections ? '#3b82f6' : '#94a3b8',
                        border: `1px solid ${hasSelections ? '#3b82f6' : '#e2e8f0'}`,
                        borderRadius: '8px',
                        fontSize: '0.8rem',
                        fontWeight: '600',
                        cursor: hasSelections ? 'pointer' : 'not-allowed',
                        transition: 'all 0.2s ease'
                    }}
                >
                    Refine Assessment
                </button>
                <button
                    onClick={() => handleSubmit(true)}
                    style={{
                        flex: 1,
                        padding: '10px',
                        background: '#3b82f6',
                        color: 'white',
                        border: 'none',
                        borderRadius: '8px',
                        fontSize: '0.8rem',
                        fontWeight: '700',
                        cursor: 'pointer',
                        transition: 'all 0.2s ease',
                        boxShadow: '0 4px 6px -1px rgba(59, 130, 246, 0.3)'
                    }}
                >
                    Finalize & Conclude
                </button>
            </div>
        </div>
    );
};

// --- 7. Physician Final Report Card ---
export const PhysicianFinalReportCard = ({ data }) => {
    const urgency = (data.urgency_level || 'Low').toLowerCase();
    const color = getRiskColor(urgency);

    return (
        <div style={{ ...cardStyle, borderLeftColor: color, background: '#fcfdfe', border: '1px solid #e0e7ff' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <span style={{ ...badgeStyle, background: '#1e293b' }}>
                    📋 Final Clinical Report
                </span>
                <span style={{ fontSize: '0.7rem', color: '#64748b', background: '#f1f5f9', padding: '2px 8px', borderRadius: '4px', fontWeight: 'bold' }}>
                    {data.urgency_level || 'Low'} Priority
                </span>
            </div>

            {data.interaction_summary && (
                <div style={{ marginBottom: '12px', padding: '10px', background: '#f8fafc', borderRadius: '8px', borderLeft: '3px solid #64748b' }}>
                    <strong style={{ ...sectionTitleStyle, color: '#475569', fontSize: '0.7rem' }}>SESSION SUMMARY</strong>
                    <p style={{ margin: '0', color: '#334155', fontSize: '0.82rem', lineHeight: '1.4' }}>{data.interaction_summary}</p>
                </div>
            )}

            <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '12px', marginBottom: '12px' }}>
                {data.technical_assessment && (
                    <div style={{ background: 'white', padding: '10px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                        <strong style={{ ...sectionTitleStyle, color: '#0f172a' }}>🩺 Technical Assessment</strong>
                        <p style={{ margin: '0', color: '#334155', fontSize: '0.85rem', lineHeight: '1.5' }}>{data.technical_assessment}</p>
                    </div>
                )}

                {data.clinical_reasoning && (
                    <div style={{ background: '#f5f3ff', padding: '10px', borderRadius: '8px', border: '1px solid #ddd6fe' }}>
                        <strong style={{ ...sectionTitleStyle, color: '#4c1d95' }}>🧠 Clinical Reasoning</strong>
                        <p style={{ margin: '0', color: '#5b21b6', fontSize: '0.82rem', lineHeight: '1.5', whiteSpace: 'pre-line' }}>{data.clinical_reasoning}</p>
                    </div>
                )}
            </div>

            {data.differential_diagnosis && data.differential_diagnosis.length > 0 && (
                <div style={{ marginBottom: '12px' }}>
                    <strong style={{ ...sectionTitleStyle, color: '#b91c1c' }}>🔬 Differential Diagnosis</strong>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '4px' }}>
                        {data.differential_diagnosis.map((d, i) => (
                            <span key={i} style={{ background: '#fef2f2', color: '#991b1b', border: '1px solid #fee2e2', padding: '2px 10px', borderRadius: '6px', fontSize: '0.75rem', fontWeight: '600' }}>
                                {d}
                            </span>
                        ))}
                    </div>
                </div>
            )}

            {data.definitive_plan && data.definitive_plan.length > 0 && (
                <div style={{ background: '#f0fdf4', padding: '12px', borderRadius: '8px', border: '1px solid #dcfce7', marginBottom: '10px' }}>
                    <strong style={{ ...sectionTitleStyle, color: '#166534' }}>📍 Definitive Clinical Plan</strong>
                    <ul style={{ ...listStyle, color: '#14532d', marginTop: '6px' }}>
                        {data.definitive_plan.map((step, i) => <li key={i} style={{ marginBottom: '4px' }}>{step}</li>)}
                    </ul>
                </div>
            )}

            {data.patient_education_summary && (
                <div style={{ padding: '8px 10px', background: '#fffbeb', borderRadius: '6px', border: '1px solid #fef3c7' }}>
                    <p style={{ margin: '0', color: '#92400e', fontSize: '0.78rem', fontStyle: 'italic' }}>
                        <strong>Note:</strong> {data.patient_education_summary}
                    </p>
                </div>
            )}

            <p style={{ ...disclaimerStyle, marginTop: '12px', textAlign: 'center', borderTop: '1px solid #e2e8f0', paddingTop: '8px' }}>
                Legal Analysis Record - LexEdge AI Professional
            </p>
        </div>
    );
};

// --- 8. Patient Onboarding Card ---
export const PatientOnboardingCard = ({ data }) => {
    const isComplete = data.is_profile_complete;

    return (
        <div style={{ ...cardStyle, borderLeftColor: isComplete ? '#10b981' : '#f59e0b', background: isComplete ? '#f0fdf4' : '#fffbeb' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
                <span style={{ ...badgeStyle, background: isComplete ? '#10b981' : '#f59e0b', fontSize: '0.65rem' }}>
                    {isComplete ? '✅ PROFILE COMPLETE' : '⏳ PROFILE INCOMPLETE'}
                </span>
            </div>

            {isComplete ? (
                <div>
                    <p style={{ fontSize: '0.85rem', fontWeight: 'bold', color: '#065f46', marginBottom: '8px' }}>
                        Thank you, {data.full_name}! Your profile is now saved.
                    </p>
                    <div style={{ background: 'white', padding: '10px', borderRadius: '8px', border: '1px solid #d1fae5' }}>
                        <p style={{ margin: '0 0 4px 0', fontSize: '0.75rem', color: '#6b7280' }}>Confirmed Details:</p>
                        <ul style={{ ...listStyle, color: '#047857', marginBottom: 0 }}>
                            <li>Age: {data.age} ({data.gender})</li>
                            <li>Allergies: {data.allergies?.join(', ') || 'None'}</li>
                            <li>Meds: {data.current_medications?.join(', ') || 'None'}</li>
                            <li><strong>Complaint: {data.chief_complaint}</strong></li>
                        </ul>
                    </div>
                </div>
            ) : (
                <div>
                    <p style={{ fontSize: '0.82rem', color: '#92400e', marginBottom: '8px', fontWeight: '500' }}>
                        We are building your clinical profile...
                    </p>
                    {data.next_question && (
                        <div style={{ background: 'white', padding: '12px', borderRadius: '8px', border: '1px solid #fef3c7', marginBottom: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.02)' }}>
                            <p style={{ margin: 0, fontSize: '0.88rem', color: '#1e293b', fontWeight: '600' }}>{data.next_question}</p>
                        </div>
                    )}
                    {data.missing_fields && data.missing_fields.length > 0 && (
                        <p style={{ fontSize: '0.7rem', color: '#b45309', margin: 0 }}>
                            Still missing: {data.missing_fields.join(', ')}
                        </p>
                    )}
                </div>
            )}
        </div>
    );
};

// --- 9. SOAP Note Card ---
export const SOAPNoteCard = ({ data }) => {
    return (
        <div style={{ ...cardStyle, borderLeftColor: '#0ea5e9', background: '#f0f9ff' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
                <span style={{ ...badgeStyle, background: '#0284c7' }}>
                    📋 SOAP Note
                </span>
            </div>
            <div style={{ marginBottom: '8px' }}>
                <strong style={{ ...sectionTitleStyle, color: '#0369a1' }}>S - Subjective</strong>
                <p style={{ margin: 0, color: '#334155', fontSize: '0.82rem', lineHeight: '1.4' }}>{data.subjective}</p>
            </div>
            <div style={{ marginBottom: '8px' }}>
                <strong style={{ ...sectionTitleStyle, color: '#0369a1' }}>O - Objective</strong>
                <p style={{ margin: 0, color: '#334155', fontSize: '0.82rem', lineHeight: '1.4' }}>{data.objective}</p>
            </div>
            <div style={{ marginBottom: '8px' }}>
                <strong style={{ ...sectionTitleStyle, color: '#0369a1' }}>A - Assessment</strong>
                <p style={{ margin: 0, color: '#334155', fontSize: '0.82rem', lineHeight: '1.4' }}>{data.assessment}</p>
            </div>
            <div style={{ marginBottom: '8px' }}>
                <strong style={{ ...sectionTitleStyle, color: '#0369a1' }}>P - Plan</strong>
                <p style={{ margin: 0, color: '#334155', fontSize: '0.82rem', lineHeight: '1.4' }}>{data.plan}</p>
            </div>
            {(data.icd_codes && data.icd_codes.length > 0) && (
                <div style={{ marginTop: '6px', fontSize: '0.75rem', color: '#475569' }}>
                    <strong>ICD-10:</strong> {data.icd_codes.join(', ')}
                </div>
            )}
            {(data.cpt_codes && data.cpt_codes.length > 0) && (
                <div style={{ fontSize: '0.75rem', color: '#475569' }}>
                    <strong>CPT:</strong> {data.cpt_codes.join(', ')}
                </div>
            )}
            <p style={disclaimerStyle}>Clinical documentation draft. Verify before use.</p>
        </div>
    );
};

// --- 10. Clinical Summary Card ---
export const ClinicalSummaryCard = ({ data }) => {
    return (
        <div style={{ ...cardStyle, borderLeftColor: '#10b981', background: '#f0fdf4' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
                <span style={{ ...badgeStyle, background: '#059669' }}>
                    🧾 Clinical Summary
                </span>
            </div>
            {data.summary_title && (
                <p style={{ margin: '0 0 8px 0', color: '#065f46', fontWeight: '700', fontSize: '0.9rem' }}>
                    {data.summary_title}
                </p>
            )}
            {data.patient_overview && (
                <div style={{ marginBottom: '8px' }}>
                    <strong style={{ ...sectionTitleStyle, color: '#047857' }}>Patient Overview</strong>
                    <p style={{ margin: 0, color: '#334155', fontSize: '0.82rem', lineHeight: '1.4' }}>{data.patient_overview}</p>
                </div>
            )}
            {data.key_findings && data.key_findings.length > 0 && (
                <div style={{ marginBottom: '8px' }}>
                    <strong style={{ ...sectionTitleStyle, color: '#047857' }}>Key Findings</strong>
                    <ul style={listStyle}>
                        {data.key_findings.map((item, i) => <li key={i}>{item}</li>)}
                    </ul>
                </div>
            )}
            {data.diagnoses && data.diagnoses.length > 0 && (
                <div style={{ marginBottom: '8px' }}>
                    <strong style={{ ...sectionTitleStyle, color: '#047857' }}>Diagnoses</strong>
                    <ul style={listStyle}>
                        {data.diagnoses.map((item, i) => <li key={i}>{item}</li>)}
                    </ul>
                </div>
            )}
            {data.treatment_plan && data.treatment_plan.length > 0 && (
                <div style={{ marginBottom: '8px' }}>
                    <strong style={{ ...sectionTitleStyle, color: '#047857' }}>Treatment Plan</strong>
                    <ul style={listStyle}>
                        {data.treatment_plan.map((item, i) => <li key={i}>{item}</li>)}
                    </ul>
                </div>
            )}
            {data.medications && data.medications.length > 0 && (
                <div style={{ marginBottom: '8px' }}>
                    <strong style={{ ...sectionTitleStyle, color: '#047857' }}>Medications</strong>
                    <ul style={listStyle}>
                        {data.medications.map((item, i) => <li key={i}>{item}</li>)}
                    </ul>
                </div>
            )}
            {data.follow_up && (
                <div style={{ marginTop: '6px', fontSize: '0.8rem', color: '#065f46' }}>
                    <strong>Follow-up:</strong> {data.follow_up}
                </div>
            )}
            <p style={disclaimerStyle}>Analysis generated by LexEdge AI.</p>
        </div>
    );
};

// --- 11. Prescription Card ---
export const PrescriptionCard = ({ data }) => {
    const hasSafetyIssues = data.safety_checks && data.safety_checks.is_safe === false;

    return (
        <div style={{ ...cardStyle, borderLeftColor: hasSafetyIssues ? '#ef4444' : '#22c55e' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
                <span style={{ ...badgeStyle, background: hasSafetyIssues ? '#dc2626' : '#16a34a' }}>
                    💊 Prescription
                </span>
            </div>

            {/* Safety Alerts */}
            {hasSafetyIssues && (
                <div style={{ background: '#fef2f2', border: '1px solid #fee2e2', borderRadius: '6px', padding: '8px', marginBottom: '10px' }}>
                    <strong style={{ ...sectionTitleStyle, color: '#b91c1c' }}>⚠️ Safety Alerts</strong>
                    {data.safety_checks?.allergy_conflicts?.map((item, idx) => (
                        <div key={`allergy-${idx}`} style={{ color: '#b91c1c', fontSize: '0.78rem' }}>🚨 {item}</div>
                    ))}
                    {data.safety_checks?.drug_interactions?.map((item, idx) => (
                        <div key={`interaction-${idx}`} style={{ color: '#b91c1c', fontSize: '0.78rem' }}>⚡ {item}</div>
                    ))}
                    {data.safety_checks?.contraindications?.map((item, idx) => (
                        <div key={`contra-${idx}`} style={{ color: '#b91c1c', fontSize: '0.78rem' }}>🚫 {item}</div>
                    ))}
                    {data.safety_checks?.dosage_warnings?.map((item, idx) => (
                        <div key={`dose-${idx}`} style={{ color: '#b91c1c', fontSize: '0.78rem' }}>💊 {item}</div>
                    ))}
                </div>
            )}

            {/* Safety Summary (when safe) */}
            {data.safety_checks?.safety_summary && data.safety_checks?.is_safe && (
                <div style={{ background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: '6px', padding: '8px', marginBottom: '10px' }}>
                    <strong style={{ ...sectionTitleStyle, color: '#166534' }}>✅ Safety Summary</strong>
                    <p style={{ margin: 0, color: '#166534', fontSize: '0.78rem' }}>{data.safety_checks.safety_summary}</p>
                </div>
            )}

            {/* Medications Table */}
            {data.medications && data.medications.length > 0 && (
                <>
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem', marginBottom: '8px' }}>
                        <thead>
                            <tr style={{ background: '#f8fafc' }}>
                                <th style={{ textAlign: 'left', padding: '6px 8px', borderBottom: '1px solid #e2e8f0', color: '#64748b', fontSize: '0.7rem' }}>Medication</th>
                                <th style={{ textAlign: 'center', padding: '6px 8px', borderBottom: '1px solid #e2e8f0', color: '#64748b', fontSize: '0.7rem' }}>Dosage</th>
                                <th style={{ textAlign: 'center', padding: '6px 8px', borderBottom: '1px solid #e2e8f0', color: '#64748b', fontSize: '0.7rem' }}>Frequency</th>
                                <th style={{ textAlign: 'center', padding: '6px 8px', borderBottom: '1px solid #e2e8f0', color: '#64748b', fontSize: '0.7rem' }}>Duration</th>
                            </tr>
                        </thead>
                        <tbody>
                            {data.medications.map((med, i) => (
                                <tr key={i} style={{ background: i % 2 === 0 ? '#ffffff' : '#f8fafc' }}>
                                    <td style={{ padding: '8px', borderBottom: '1px solid #f1f5f9', fontWeight: '600', color: '#1f2937' }}>
                                        {med.drug_name}
                                        {med.generic_name && <span style={{ fontWeight: '400', color: '#6b7280', fontSize: '0.75rem' }}> ({med.generic_name})</span>}
                                    </td>
                                    <td style={{ padding: '8px', borderBottom: '1px solid #f1f5f9', textAlign: 'center' }}>{med.dosage}</td>
                                    <td style={{ padding: '8px', borderBottom: '1px solid #f1f5f9', textAlign: 'center' }}>{med.frequency}</td>
                                    <td style={{ padding: '8px', borderBottom: '1px solid #f1f5f9', textAlign: 'center' }}>{med.duration}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>

                    {/* Detailed Drug Information for each medication */}
                    {data.medications.map((med, i) => (
                        <div key={`detail-${i}`} style={{ background: '#f8fafc', padding: '10px', borderRadius: '6px', border: '1px solid #e2e8f0', marginBottom: '8px' }}>
                            <strong style={{ color: '#1e40af', fontSize: '0.85rem' }}>📋 {med.drug_name} Details</strong>

                            {med.drug_class && (
                                <p style={{ margin: '4px 0', fontSize: '0.78rem', color: '#475569' }}>
                                    <strong>Class:</strong> {med.drug_class}
                                </p>
                            )}

                            {med.mechanism_of_action && (
                                <p style={{ margin: '4px 0', fontSize: '0.78rem', color: '#475569' }}>
                                    <strong>How it works:</strong> {med.mechanism_of_action}
                                </p>
                            )}

                            {med.instructions && (
                                <p style={{ margin: '4px 0', fontSize: '0.78rem', color: '#475569' }}>
                                    <strong>Instructions:</strong> {med.instructions}
                                </p>
                            )}

                            {med.food_interactions && (
                                <p style={{ margin: '4px 0', fontSize: '0.78rem', color: '#475569' }}>
                                    <strong>Food interactions:</strong> {med.food_interactions}
                                </p>
                            )}

                            {/* Side Effects */}
                            {med.common_side_effects && med.common_side_effects.length > 0 && (
                                <div style={{ marginTop: '6px' }}>
                                    <strong style={{ fontSize: '0.75rem', color: '#f59e0b' }}>⚡ Common Side Effects:</strong>
                                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginTop: '4px' }}>
                                        {Array.isArray(med.common_side_effects) ? med.common_side_effects.map((se, idx) => (
                                            <span key={idx} style={{ background: '#fef3c7', color: '#92400e', padding: '2px 6px', borderRadius: '4px', fontSize: '0.7rem' }}>{se}</span>
                                        )) : (
                                            <span style={{ background: '#fef3c7', color: '#92400e', padding: '2px 6px', borderRadius: '4px', fontSize: '0.7rem' }}>{med.common_side_effects}</span>
                                        )}
                                    </div>
                                </div>
                            )}

                            {med.serious_side_effects && med.serious_side_effects.length > 0 && (
                                <div style={{ marginTop: '6px' }}>
                                    <strong style={{ fontSize: '0.75rem', color: '#dc2626' }}>🚨 Serious Side Effects (seek help):</strong>
                                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginTop: '4px' }}>
                                        {Array.isArray(med.serious_side_effects) ? med.serious_side_effects.map((se, idx) => (
                                            <span key={idx} style={{ background: '#fee2e2', color: '#991b1b', padding: '2px 6px', borderRadius: '4px', fontSize: '0.7rem' }}>{se}</span>
                                        )) : (
                                            <span style={{ background: '#fee2e2', color: '#991b1b', padding: '2px 6px', borderRadius: '4px', fontSize: '0.7rem' }}>{med.serious_side_effects}</span>
                                        )}
                                    </div>
                                </div>
                            )}

                            {/* Precautions */}
                            {med.precautions && med.precautions.length > 0 && (
                                <div style={{ marginTop: '6px' }}>
                                    <strong style={{ fontSize: '0.75rem', color: '#7c3aed' }}>⚠️ Precautions:</strong>
                                    <ul style={{ ...listStyle, marginTop: '4px' }}>
                                        {Array.isArray(med.precautions) ? med.precautions.map((p, idx) => <li key={idx}>{p}</li>) : <li>{med.precautions}</li>}
                                    </ul>
                                </div>
                            )}

                            {med.when_to_seek_help && (
                                <p style={{ margin: '6px 0 0 0', fontSize: '0.78rem', color: '#dc2626', fontWeight: '500' }}>
                                    🏥 <strong>When to seek help:</strong> {med.when_to_seek_help}
                                </p>
                            )}
                        </div>
                    ))}
                </>
            )}

            {/* Patient Instructions */}
            {data.patient_instructions && (
                <div style={{ background: '#eff6ff', padding: '8px', borderRadius: '6px', border: '1px solid #bfdbfe', marginBottom: '8px' }}>
                    <strong style={{ ...sectionTitleStyle, color: '#1e40af' }}>📝 Instructions</strong>
                    <p style={{ margin: 0, color: '#1e3a8a', fontSize: '0.8rem' }}>{data.patient_instructions}</p>
                </div>
            )}

            {/* Lifestyle Recommendations */}
            {data.lifestyle_recommendations && data.lifestyle_recommendations.length > 0 && (
                <div style={{ background: '#f0fdf4', padding: '8px', borderRadius: '6px', border: '1px solid #bbf7d0', marginBottom: '8px' }}>
                    <strong style={{ ...sectionTitleStyle, color: '#166534' }}>🌿 Lifestyle Recommendations</strong>
                    <ul style={{ ...listStyle, color: '#166534' }}>
                        {data.lifestyle_recommendations.map((rec, i) => <li key={i}>{rec}</li>)}
                    </ul>
                </div>
            )}

            {/* Follow-up */}
            {data.follow_up && (
                <div style={{ background: '#faf5ff', padding: '8px', borderRadius: '6px', border: '1px solid #e9d5ff', marginBottom: '8px' }}>
                    <strong style={{ ...sectionTitleStyle, color: '#7c3aed' }}>📅 Follow-up</strong>
                    <p style={{ margin: 0, color: '#6b21a8', fontSize: '0.8rem' }}>{data.follow_up}</p>
                </div>
            )}

            {/* Follow-up Q&A */}
            {data.follow_up_questions && data.follow_up_questions.length > 0 && (
                <div style={{ background: '#fefce8', padding: '8px', borderRadius: '6px', border: '1px solid #fef08a', marginBottom: '8px' }}>
                    <strong style={{ ...sectionTitleStyle, color: '#a16207' }}>❓ Common Questions</strong>
                    {data.follow_up_questions.map((qa, i) => (
                        <div key={i} style={{ marginTop: '6px', paddingTop: '6px', borderTop: i > 0 ? '1px solid #fef08a' : 'none' }}>
                            <p style={{ margin: 0, fontWeight: '600', color: '#92400e', fontSize: '0.78rem' }}>Q: {qa.question}</p>
                            <p style={{ margin: '2px 0 0 0', color: '#78350f', fontSize: '0.78rem' }}>A: {qa.answer}</p>
                        </div>
                    ))}
                </div>
            )}

            <p style={disclaimerStyle}>Prescription draft. Confirm with licensed provider.</p>
        </div>
    );
};

// --- 12. Patient Education Card ---
export const PatientEducationCard = ({ data }) => {
    return (
        <div style={{ ...cardStyle, borderLeftColor: '#6366f1', background: '#eef2ff' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
                <span style={{ ...badgeStyle, background: '#4f46e5' }}>
                    📚 Patient Education
                </span>
            </div>
            {data.title && (
                <p style={{ margin: '0 0 8px 0', color: '#312e81', fontWeight: '700', fontSize: '0.9rem' }}>
                    {data.title}
                </p>
            )}
            {data.simple_explanation && (
                <div style={{ marginBottom: '8px' }}>
                    <strong style={{ ...sectionTitleStyle, color: '#4338ca' }}>Simple Explanation</strong>
                    <p style={{ margin: 0, color: '#334155', fontSize: '0.82rem', lineHeight: '1.4' }}>{data.simple_explanation}</p>
                </div>
            )}
            {data.what_it_means && (
                <div style={{ marginBottom: '8px' }}>
                    <strong style={{ ...sectionTitleStyle, color: '#4338ca' }}>What It Means</strong>
                    <p style={{ margin: 0, color: '#334155', fontSize: '0.82rem', lineHeight: '1.4' }}>{data.what_it_means}</p>
                </div>
            )}
            {data.what_to_do && data.what_to_do.length > 0 && (
                <div style={{ marginBottom: '8px' }}>
                    <strong style={{ ...sectionTitleStyle, color: '#4338ca' }}>What To Do</strong>
                    <ul style={listStyle}>
                        {data.what_to_do.map((item, i) => <li key={i}>{item}</li>)}
                    </ul>
                </div>
            )}
            {data.what_to_avoid && data.what_to_avoid.length > 0 && (
                <div style={{ marginBottom: '8px' }}>
                    <strong style={{ ...sectionTitleStyle, color: '#4338ca' }}>What To Avoid</strong>
                    <ul style={listStyle}>
                        {data.what_to_avoid.map((item, i) => <li key={i}>{item}</li>)}
                    </ul>
                </div>
            )}
            {data.when_to_seek_help && data.when_to_seek_help.length > 0 && (
                <div style={{ marginBottom: '8px', background: '#fef2f2', padding: '8px', borderRadius: '6px', border: '1px solid #fee2e2' }}>
                    <strong style={{ ...sectionTitleStyle, color: '#b91c1c' }}>When To Seek Help</strong>
                    <ul style={{ ...listStyle, color: '#b91c1c' }}>
                        {data.when_to_seek_help.map((item, i) => <li key={i}>{item}</li>)}
                    </ul>
                </div>
            )}
            <p style={disclaimerStyle}>Educational content only. Follow clinician advice.</p>
        </div>
    );
};

// --- 13. General Card ---
export const GeneralCard = ({ data }) => {
    return (
        <div style={{ padding: '4px 0' }}>
            <div dangerouslySetInnerHTML={{ __html: data.content || data.text }} />
        </div>
    );
};

// ============================================
// LEGAL RESPONSE CARDS
// ============================================

// --- Legal Analysis Card ---
export const LegalAnalysisCard = ({ data }) => {
    const riskLevel = data.analysis?.risk_level || 'moderate';
    const riskColor = riskLevel === 'high' ? '#ef4444' : riskLevel === 'low' ? '#22c55e' : '#eab308';
    
    return (
        <div style={{ ...cardStyle, borderLeftColor: '#6366f1', background: '#f5f3ff' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
                <span style={{ ...badgeStyle, background: '#6366f1' }}>
                    ⚖️ Legal Analysis
                </span>
                <span style={{ ...badgeStyle, background: riskColor }}>
                    {riskLevel} Risk
                </span>
            </div>
            
            {data.client_name && (
                <p style={{ margin: '0 0 8px 0', color: '#4338ca', fontWeight: '600', fontSize: '0.85rem' }}>
                    Client: {data.client_name} | Jurisdiction: {data.jurisdiction}
                </p>
            )}
            
            {data.analysis?.legal_issues && (
                <div style={{ marginBottom: '8px' }}>
                    <strong style={{ ...sectionTitleStyle, color: '#4338ca' }}>Legal Issues</strong>
                    <p style={{ margin: 0, color: '#334155', fontSize: '0.82rem' }}>{data.analysis.legal_issues}</p>
                </div>
            )}
            
            {data.analysis?.recommended_actions && data.analysis.recommended_actions.length > 0 && (
                <div style={{ marginBottom: '8px' }}>
                    <strong style={{ ...sectionTitleStyle, color: '#4338ca' }}>Recommended Actions</strong>
                    <ul style={listStyle}>
                        {data.analysis.recommended_actions.map((item, i) => <li key={i}>{item}</li>)}
                    </ul>
                </div>
            )}
            
            {data.analysis?.next_steps && data.analysis.next_steps.length > 0 && (
                <div style={{ marginBottom: '8px', background: '#eff6ff', padding: '8px', borderRadius: '6px' }}>
                    <strong style={{ ...sectionTitleStyle, color: '#1e40af' }}>Next Steps</strong>
                    <ul style={listStyle}>
                        {data.analysis.next_steps.map((item, i) => <li key={i}>{item}</li>)}
                    </ul>
                </div>
            )}
            
            {data.disclaimers && data.disclaimers.length > 0 && (
                <div style={{ background: '#fef3c7', padding: '6px 8px', borderRadius: '6px', marginTop: '8px' }}>
                    {data.disclaimers.map((d, i) => (
                        <p key={i} style={{ ...disclaimerStyle, color: '#92400e', fontStyle: 'normal' }}>{d}</p>
                    ))}
                </div>
            )}
        </div>
    );
};

// --- Contract Review Card ---
export const ContractReviewCard = ({ data }) => {
    return (
        <div style={{ ...cardStyle, borderLeftColor: '#0891b2', background: '#ecfeff' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
                <span style={{ ...badgeStyle, background: '#0891b2' }}>
                    📄 Contract Review
                </span>
            </div>
            
            {data.review?.executive_summary && (
                <div style={{ marginBottom: '8px' }}>
                    <strong style={{ ...sectionTitleStyle, color: '#0e7490' }}>Executive Summary</strong>
                    <p style={{ margin: 0, color: '#334155', fontSize: '0.82rem' }}>{data.review.executive_summary}</p>
                </div>
            )}
            
            {data.review?.risk_assessment && (
                <div style={{ marginBottom: '8px' }}>
                    <strong style={{ ...sectionTitleStyle, color: '#0e7490' }}>Risk Assessment</strong>
                    {data.review.risk_assessment.high_risk_clauses && (
                        <div style={{ background: '#fef2f2', padding: '6px', borderRadius: '4px', marginBottom: '4px' }}>
                            <span style={{ fontSize: '0.75rem', color: '#b91c1c', fontWeight: '600' }}>High Risk:</span>
                            <ul style={{ ...listStyle, color: '#b91c1c' }}>
                                {data.review.risk_assessment.high_risk_clauses.map((item, i) => <li key={i}>{item}</li>)}
                            </ul>
                        </div>
                    )}
                    {data.review.risk_assessment.medium_risk_clauses && (
                        <div style={{ background: '#fef9c3', padding: '6px', borderRadius: '4px', marginBottom: '4px' }}>
                            <span style={{ fontSize: '0.75rem', color: '#a16207', fontWeight: '600' }}>Medium Risk:</span>
                            <ul style={{ ...listStyle, color: '#a16207' }}>
                                {data.review.risk_assessment.medium_risk_clauses.map((item, i) => <li key={i}>{item}</li>)}
                            </ul>
                        </div>
                    )}
                </div>
            )}
            
            {data.review?.recommended_changes && data.review.recommended_changes.length > 0 && (
                <div style={{ marginBottom: '8px' }}>
                    <strong style={{ ...sectionTitleStyle, color: '#0e7490' }}>Recommended Changes</strong>
                    <ul style={listStyle}>
                        {data.review.recommended_changes.map((item, i) => <li key={i}>{item}</li>)}
                    </ul>
                </div>
            )}
            
            <p style={disclaimerStyle}>{data.disclaimer || 'Review with licensed counsel before signing.'}</p>
        </div>
    );
};

// --- Legal Research Card ---
export const LegalResearchCard = ({ data }) => {
    return (
        <div style={{ ...cardStyle, borderLeftColor: '#8b5cf6', background: '#faf5ff' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
                <span style={{ ...badgeStyle, background: '#8b5cf6' }}>
                    🔍 Legal Research
                </span>
                {data.jurisdiction && (
                    <span style={{ fontSize: '0.75rem', color: '#6b21a8' }}>
                        {data.jurisdiction}
                    </span>
                )}
            </div>
            
            {data.results?.cases && data.results.cases.length > 0 && (
                <div style={{ marginBottom: '8px' }}>
                    <strong style={{ ...sectionTitleStyle, color: '#7c3aed' }}>Relevant Cases</strong>
                    {data.results.cases.map((c, i) => (
                        <div key={i} style={{ background: '#f5f3ff', padding: '6px', borderRadius: '4px', marginBottom: '4px' }}>
                            <p style={{ margin: 0, fontWeight: '600', fontSize: '0.8rem', color: '#5b21b6' }}>{c.case_name}</p>
                            <p style={{ margin: 0, fontSize: '0.75rem', color: '#6b7280' }}>{c.citation}</p>
                            <p style={{ margin: '4px 0 0', fontSize: '0.78rem', color: '#334155' }}>{c.key_holding}</p>
                        </div>
                    ))}
                </div>
            )}
            
            {data.results?.legal_principles && data.results.legal_principles.length > 0 && (
                <div style={{ marginBottom: '8px' }}>
                    <strong style={{ ...sectionTitleStyle, color: '#7c3aed' }}>Legal Principles</strong>
                    <ul style={listStyle}>
                        {data.results.legal_principles.map((item, i) => <li key={i}>{item}</li>)}
                    </ul>
                </div>
            )}
            
            <p style={disclaimerStyle}>{data.disclaimer || 'Verify all citations independently.'}</p>
        </div>
    );
};

// --- Case Management Card ---
export const CaseManagementCard = ({ data }) => {
    return (
        <div style={{ ...cardStyle, borderLeftColor: '#059669', background: '#ecfdf5' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
                <span style={{ ...badgeStyle, background: '#059669' }}>
                    📋 Case Management
                </span>
            </div>
            
            {data.case_name && (
                <p style={{ margin: '0 0 8px 0', color: '#047857', fontWeight: '600', fontSize: '0.85rem' }}>
                    {data.case_name}
                </p>
            )}
            
            {data.deadlines?.upcoming && data.deadlines.upcoming.length > 0 && (
                <div style={{ marginBottom: '8px' }}>
                    <strong style={{ ...sectionTitleStyle, color: '#047857' }}>Upcoming Deadlines</strong>
                    {data.deadlines.upcoming.map((d, i) => (
                        <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: '1px solid #d1fae5' }}>
                            <span style={{ fontSize: '0.8rem', color: '#334155' }}>{d.type}: {d.description}</span>
                            <span style={{ fontSize: '0.75rem', color: d.priority === 'High' ? '#dc2626' : '#6b7280', fontWeight: '600' }}>{d.date}</span>
                        </div>
                    ))}
                </div>
            )}
            
            {data.timeline?.phases && data.timeline.phases.length > 0 && (
                <div style={{ marginBottom: '8px' }}>
                    <strong style={{ ...sectionTitleStyle, color: '#047857' }}>Case Timeline</strong>
                    {data.timeline.phases.map((p, i) => (
                        <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '4px 0' }}>
                            <span style={{ 
                                width: '8px', height: '8px', borderRadius: '50%', 
                                background: p.status === 'Completed' ? '#22c55e' : p.status === 'In Progress' ? '#eab308' : '#d1d5db'
                            }}></span>
                            <span style={{ fontSize: '0.8rem', color: '#334155' }}>{p.phase}</span>
                            <span style={{ fontSize: '0.7rem', color: '#6b7280' }}>({p.status})</span>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

// --- Compliance Card ---
export const ComplianceCard = ({ data }) => {
    return (
        <div style={{ ...cardStyle, borderLeftColor: '#dc2626', background: '#fef2f2' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
                <span style={{ ...badgeStyle, background: '#dc2626' }}>
                    🛡️ Compliance Review
                </span>
                {data.overall_assessment?.status && (
                    <span style={{ fontSize: '0.75rem', color: '#991b1b', fontWeight: '600' }}>
                        Status: {data.overall_assessment.status}
                    </span>
                )}
            </div>
            
            {data.frameworks_audited && data.frameworks_audited.length > 0 && (
                <div style={{ marginBottom: '8px' }}>
                    <strong style={{ ...sectionTitleStyle, color: '#b91c1c' }}>Frameworks Audited</strong>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                        {data.frameworks_audited.map((f, i) => (
                            <span key={i} style={{ background: '#fee2e2', padding: '2px 8px', borderRadius: '4px', fontSize: '0.75rem', color: '#991b1b' }}>
                                {f}
                            </span>
                        ))}
                    </div>
                </div>
            )}
            
            {data.overall_assessment?.priority_areas && data.overall_assessment.priority_areas.length > 0 && (
                <div style={{ marginBottom: '8px' }}>
                    <strong style={{ ...sectionTitleStyle, color: '#b91c1c' }}>Priority Areas</strong>
                    <ul style={listStyle}>
                        {data.overall_assessment.priority_areas.map((item, i) => <li key={i}>{item}</li>)}
                    </ul>
                </div>
            )}
            
            {data.overall_assessment?.next_steps && data.overall_assessment.next_steps.length > 0 && (
                <div style={{ marginBottom: '8px', background: '#fef9c3', padding: '8px', borderRadius: '6px' }}>
                    <strong style={{ ...sectionTitleStyle, color: '#a16207' }}>Next Steps</strong>
                    <ul style={{ ...listStyle, color: '#a16207' }}>
                        {data.overall_assessment.next_steps.map((item, i) => <li key={i}>{item}</li>)}
                    </ul>
                </div>
            )}
            
            <p style={disclaimerStyle}>{data.disclaimer || 'Conduct formal compliance assessment with qualified professionals.'}</p>
        </div>
    );
};

// --- Legal Correspondence Card ---
export const LegalCorrespondenceCard = ({ data }) => {
    return (
        <div style={{ ...cardStyle, borderLeftColor: '#2563eb', background: '#eff6ff' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
                <span style={{ ...badgeStyle, background: '#2563eb' }}>
                    ✉️ Legal Correspondence
                </span>
            </div>
            
            {data.letter?.header && (
                <div style={{ marginBottom: '8px', borderBottom: '1px solid #bfdbfe', paddingBottom: '8px' }}>
                    <p style={{ margin: 0, fontWeight: '600', fontSize: '0.85rem', color: '#1e40af' }}>{data.letter.header.title}</p>
                    <p style={{ margin: '4px 0 0', fontSize: '0.78rem', color: '#6b7280' }}>To: {data.letter.header.to || data.letter.header.recipient}</p>
                    <p style={{ margin: 0, fontSize: '0.78rem', color: '#6b7280' }}>Date: {data.letter.header.date}</p>
                </div>
            )}
            
            {data.letter?.body && (
                <div style={{ marginBottom: '8px' }}>
                    {typeof data.letter.body === 'string' ? (
                        <p style={{ margin: 0, fontSize: '0.82rem', color: '#334155', whiteSpace: 'pre-wrap' }}>{data.letter.body}</p>
                    ) : (
                        Object.entries(data.letter.body).map(([key, value], i) => (
                            <div key={i} style={{ marginBottom: '6px' }}>
                                <strong style={{ ...sectionTitleStyle, color: '#1e40af', textTransform: 'capitalize' }}>{key.replace(/_/g, ' ')}</strong>
                                <p style={{ margin: 0, fontSize: '0.8rem', color: '#334155' }}>{value}</p>
                            </div>
                        ))
                    )}
                </div>
            )}
            
            <p style={disclaimerStyle}>{data.disclaimer || 'Review with licensed counsel before sending.'}</p>
        </div>
    );
};
