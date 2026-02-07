// src/components/WorkoutSuggestion.jsx
function WorkoutSuggestion({ workout }) {
  if (!workout) return null;

  return (
    <div className="workout-card">
      <h3>{workout.name}</h3>
      <div className="exercise-list">
        {workout.exercises.map((exercise, index) => (
          <div key={index} className="exercise-item">
            <h4>{exercise.name}</h4>
            <p>Sets: {exercise.sets} | Reps: {exercise.reps}</p>
            {exercise.equipment && <span>Equipment: {exercise.equipment}</span>}
          </div>
        ))}
      </div>
    </div>
  );
}

export default WorkoutSuggestion;