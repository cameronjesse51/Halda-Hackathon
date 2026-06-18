import { useEffect, useRef } from 'react'

/**
 * Renders a list of scholarship search results as clickable cards.
 * Each card links directly to the source so the student can apply.
 */
export default function ScholarshipResults({ resultSet }) {
  const scholarships = resultSet?.scholarships || []
  const usedFallback = resultSet?.used_fallback === true
  const query = resultSet?.query || ''
  const listRef = useRef(null)

  // Staggered entrance animation — mirrors CollegeCard pattern
  useEffect(() => {
    const cards = listRef.current?.querySelectorAll('.scholarship-card')
    if (!cards) return
    cards.forEach((card, i) => {
      card.style.opacity = '0'
      card.style.transform = 'translateY(16px)'
      setTimeout(() => {
        card.style.transition = 'opacity 0.35s ease, transform 0.35s ease'
        card.style.opacity = '1'
        card.style.transform = 'translateY(0)'
      }, i * 80)
    })
  }, [scholarships])

  if (!scholarships.length) return null

  return (
    <section className="scholarship-results" aria-label="Scholarship search results">
      <div className="scholarship-results-heading">
        <div>
          <h2 className="scholarship-results-title">
            🎓 {scholarships.length} scholarship {scholarships.length === 1 ? 'result' : 'results'}
          </h2>
          {usedFallback ? (
            <p className="scholarship-fallback-note">
              Live search wasn't available — here are trusted places to start your search.
            </p>
          ) : (
            <p className="scholarship-query-note">for: <em>{query}</em></p>
          )}
        </div>
      </div>

      <div className="scholarship-card-list" ref={listRef}>
        {scholarships.map((s, i) => (
          <a
            key={i}
            href={s.url}
            target="_blank"
            rel="noopener noreferrer"
            className="scholarship-card"
            aria-label={`${s.title} — opens in new tab`}
          >
            <div className="scholarship-card-header">
              <span className="scholarship-title">{s.title}</span>
              {s.is_trusted_source && (
                <span className="scholarship-trusted-badge" title="Trusted scholarship source">
                  ✓ Trusted
                </span>
              )}
            </div>

            {s.description && (
              <p className="scholarship-description">{s.description}</p>
            )}

            <div className="scholarship-card-footer">
              <span className="scholarship-source">{s.source}</span>
              <span className="scholarship-cta">Apply →</span>
            </div>
          </a>
        ))}
      </div>

      <p className="scholarship-extra-tip">
        💡 Also check your school's financial aid office and your state's higher education authority for local awards.
      </p>
    </section>
  )
}
