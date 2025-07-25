import math, random, copy
import numpy as np

# SIS (Sequential Importance Random Sampling)

class Particle:
    def __init__(self, x, y, weight=1.0):
        self.x = x
        self.y = y
        self.weight = weight

class ParticleFilter:
    def __init__(self, N_s, width, height):
        self.N_s = N_s
        # self.particles = [Particle(random.uniform(0, width), random.uniform(0, height), weight=1.0 / N_s) for _ in range(N_s)]

        # or, we could spread uniformly around the true start position. this will cause faster convergence of the particles
        # mitigating error at the start. 
        deviation = 200
        self.particles = [Particle(random.uniform(700 - deviation, 700 + deviation), random.uniform(250 - deviation, 250 + deviation), weight=1.0 / N_s) for _ in range(N_s)]

    def predict(self, mu, dt):
        # I need to come up with an importance density. 
        # I will use the prior for this task (bootstrap filter). 
        for p in self.particles:
            motion_uncertainty_predict = random.betavariate(5, 2)
            angle = random.uniform(0, 2 * math.pi)
            r = random.gauss(0.0, 8.0)
            # x = x_0 + v_x*dt + noise
            # y = y_0 + v_y*dt + noise
            p.x += (mu[0] * motion_uncertainty_predict) * dt + r * math.cos(angle)
            p.y += (mu[1] * motion_uncertainty_predict) * dt + r * math.sin(angle)

    def update(self, z_k, beacon_positions, sensor_std):
        sum_weights = 0.0
        for p in self.particles:
            # update weight for each particle recursively
            for z_k_i, beacon_pos in zip(z_k, beacon_positions):
                dx = p.x - beacon_pos[0]
                dy = p.y - beacon_pos[1]
                dist = np.sqrt(dx**2 + dy**2)

                error = z_k_i - dist
                coeff = 1.0 / (np.sqrt(2 * np.pi) * sensor_std)
                exponent = - (error ** 2) / (2 * sensor_std ** 2)
                likelihood = coeff * np.exp(exponent)

                p.weight *= likelihood  # assuming independence

            sum_weights += p.weight

        # normalize particles to form valid pdf
        for p in self.particles:
            p.weight /= sum_weights

    def resample(self):
        # approximate effective sample size. 
        N_s = self.N_s
        particles = self.particles

        # systematic resampling as detailed by Arulampalam et al. (2002)
        cdf = [particles[0].weight]
        for i in range(1, N_s):
            cdf.append(cdf[-1] + particles[i].weight)
        u1 = random.uniform(0, 1.0 / N_s)
        i = 0
        new_particles = []
        for j in range(N_s):
            uj = u1 + j / N_s
            while uj > cdf[i]:
                i += 1
            selected = copy.deepcopy(particles[i])
            selected.weight = 1.0 / N_s
            new_particles.append(selected)
        self.particles = new_particles

    def effective_sample_size(self):
        # compute approximated N_eff (effective sample size) 
        sum_sq_weights = sum(p.weight ** 2 for p in self.particles)
        return 1.0 / sum_sq_weights

    def get_estimated_state(self):
        x = sum(p.x for p in self.particles) / self.N_s
        y = sum(p.y for p in self.particles) / self.N_s
        return np.array([x, y])
