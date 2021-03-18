import numpy as np
import matplotlib.pyplot as plt
import matplotlib


def Normal(x, mu, sigma):
    # Normal distribution
    return 1 / (2*np.pi*sigma)**(1/2) * np.exp(- (x - mu)**2 / (2 * sigma)) 

def g(v):
    return v**2

def dg_dphi(v):
    return 2*v


def fig_2b(CU):
    
    def dphi_dt(phi, e_p, e_u):
        return e_u * dg_dphi(phi) - e_p

    def dep_dt(phi, e_p, e_u):
        return phi - v_p - sigma_p * e_p

    def deu_dt(phi, e_p, e_u):
        return u - g(phi) - sigma_u * e_u

    def grad_descent(tau=1, w_phi=1, w_ep=1, w_eu=1):
        trace    = np.zeros((steps, 3))
        state    = (phi, e_p, e_u)
        trace[0] = np.asarray(state)
        for t in range(steps-1):
            state += dt / tau * np.array([w_phi*dphi_dt(*state), w_ep*dep_dt(*state), w_eu*deu_dt(*state)])
            trace[t+1] = np.asarray(state)
        return trace    
            
        

    u       = 2
    sigma_u = 1
    v_p     = 3
    sigma_p = 1
    phi     = v_p
    e_p     = 0
    e_u     = 0
    dt      = 0.001
    dur     = 10
    steps   = int(dur/dt)



    states = grad_descent(tau=1, w_phi= phi, w_ep= e_p, w_eu= e_u)
    print (states)
    

    
fig_2b(True)