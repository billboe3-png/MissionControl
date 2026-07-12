interface ResumeCardProps {
    available: boolean;
    title: string | null;
    description: string | null;
}

export default function ResumeCard({
    available,
    title,
    description,
}: ResumeCardProps) {
    return (
        <div className="card">
            <h2>Resume</h2>

            {available ? (
                <>
                    <span className="badge badge-success">Available</span>
                    {title && <strong>{title}</strong>}
                    {description && <p>{description}</p>}
                </>
            ) : (
                <>
                    <span className="badge badge-muted">Not Available</span>
                    <p className="muted-text">
                        No work currently waiting to be resumed.
                    </p>
                </>
            )}
        </div>
    );
}
