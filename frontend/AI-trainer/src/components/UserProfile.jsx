import { useState } from 'react';
import { api } from '../config/api';

function UserProfile() {
  const [formData, setFormData] = useState({
    name: '',
    age: '',
    gender: 'male',
    weight_kg: '',
    height_cm: '',
    fitness_level: 'beginner',
    goals: [],
    medical_conditions: []
  });
  const [userId, setUserId] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      // Convert strings to numbers
      const userData = {
        ...formData,
        age: parseInt(formData.age),
        weight_kg: parseFloat(formData.weight_kg),
        height_cm: parseFloat(formData.height_cm),
        goals: formData.goals.length ? formData.goals : ['General Fitness']
      };

      const result = await api.createUser(userData);
      setUserId(result.user_id);
      alert(`Welcome ${result.message}! Your BMI: ${result.bmi}`);
    } catch (error) {
      alert('Error creating profile: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="user-profile">
      <h2>Create Your Profile</h2>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="Name"
          value={formData.name}
          onChange={(e) => setFormData({...formData, name: e.target.value})}
          required
        />
        <input
          type="number"
          placeholder="Age"
          value={formData.age}
          onChange={(e) => setFormData({...formData, age: e.target.value})}
          required
        />
        <select
          value={formData.gender}
          onChange={(e) => setFormData({...formData, gender: e.target.value})}
        >
          <option value="male">Male</option>
          <option value="female">Female</option>
          <option value="other">Other</option>
        </select>
        <input
          type="number"
          placeholder="Weight (kg)"
          value={formData.weight_kg}
          onChange={(e) => setFormData({...formData, weight_kg: e.target.value})}
          required
        />
        <input
          type="number"
          placeholder="Height (cm)"
          value={formData.height_cm}
          onChange={(e) => setFormData({...formData, height_cm: e.target.value})}
          required
        />
        <select
          value={formData.fitness_level}
          onChange={(e) => setFormData({...formData, fitness_level: e.target.value})}
        >
          <option value="beginner">Beginner</option>
          <option value="intermediate">Intermediate</option>
          <option value="advanced">Advanced</option>
        </select>
        <button type="submit" disabled={loading}>
          {loading ? 'Creating...' : 'Create Profile'}
        </button>
      </form>
      {userId && <p>Your User ID: {userId}</p>}
    </div>
  );
}

export default UserProfile;