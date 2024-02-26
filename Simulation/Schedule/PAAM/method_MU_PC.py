import casadi
import numpy as np



def SolvePC_D(W_ZF, W_A, W_D_init=None):
    ueNum = np.shape(W_ZF)[1]

    W_ZF_real = np.real(W_ZF)
    W_ZF_imag = np.imag(W_ZF)
    W_D_col = casadi.MX.sym('W_D', 2*ueNum*ueNum, 1)
    W_D = casadi.reshape(W_D_col, 2*ueNum, ueNum)
    W_D_real = W_D[:ueNum, :]
    W_D_imag = W_D[ueNum:, :]
    W_A_real = np.real(W_A)
    W_A_imag = np.imag(W_A)

    W_D_init_temp = np.exp(1j*np.random.uniform(0, 2*np.pi, (ueNum, ueNum))) if W_D_init is None else W_D_init
    W_D_init_real = np.real(W_D_init_temp)
    W_D_init_imag = np.imag(W_D_init_temp)

    error_real = W_ZF_real - casadi.mtimes(W_A_real, W_D_real) + casadi.mtimes(W_A_imag, W_D_imag)
    error_imag = W_ZF_imag - casadi.mtimes(W_A_real, W_D_imag) - casadi.mtimes(W_A_imag, W_D_real)
    error = casadi.sum2(casadi.sum1(error_real**2+error_imag**2))

    input = {
        'x': W_D_col,
        'f': error}
    ipopt_opt = {
        'print_time': False,
        'ipopt.print_level': 0, 
        'ipopt.max_iter': 1000}
    solver = casadi.nlpsol('solver', 'ipopt', input, ipopt_opt)
    output = solver(x0=np.concatenate((
        np.reshape(W_D_init_real, (ueNum*ueNum), order='F'), 
        np.reshape(W_D_init_imag, (ueNum*ueNum), order='F'))))

    W_D_col = casadi.reshape(output['x'], 2*ueNum, ueNum)
    W_D = np.array(W_D_col[:ueNum, :]) + 1j * np.array(W_D_col[ueNum:, :])
    return W_D

def SolvePC_A(W_ZF, W_D, W_A_init=None, W_A_mask=None, hard=False):
    elemNum = np.shape(W_ZF)[0]
    ueNum = np.shape(W_ZF)[1]

    W_ZF_real = np.real(W_ZF)
    W_ZF_imag = np.imag(W_ZF)
    W_D_real = np.real(W_D)
    W_D_imag = np.imag(W_D)
    W_A_col = casadi.MX.sym('W_A', 2*elemNum*ueNum, 1)
    W_A_real_col = W_A_col[elemNum*ueNum:]
    W_A_imag_col = W_A_col[:elemNum*ueNum]
    W_A_real = casadi.reshape(W_A_real_col, elemNum, ueNum)
    W_A_imag = casadi.reshape(W_A_imag_col, elemNum, ueNum)

    W_A_init_temp = np.exp(1j*np.random.uniform(0, 2*np.pi, (elemNum, ueNum))) if W_A_init is None else W_A_init
    W_A_init_real = np.real(W_A_init_temp)
    W_A_init_imag = np.imag(W_A_init_temp)

    W_A_power = W_A_real_col ** 2 + W_A_imag_col ** 2
    W_A_power_max = +np.inf if not hard else 1.0
    W_A_power_min = -np.inf if not hard else 1.0

    W_A_mask_temp = np.ones((elemNum, ueNum)) if W_A_mask is None else W_A_mask
    
    error_real = W_ZF_real - \
        casadi.mtimes(casadi.times(W_A_mask_temp, W_A_real), W_D_real) + \
        casadi.mtimes(casadi.times(W_A_mask_temp, W_A_imag), W_D_imag)
    error_imag = W_ZF_imag - \
        casadi.mtimes(casadi.times(W_A_mask_temp, W_A_real), W_D_imag) - \
        casadi.mtimes(casadi.times(W_A_mask_temp, W_A_imag), W_D_real)
    error = casadi.sum2(casadi.sum1(error_real**2+error_imag**2))

    input = {
        'x': W_A_col, 
        'f': error,
        'g': W_A_power}
    ipopt_opt = {
        'print_time': False,
        'ipopt.print_level': 0, 
        'ipopt.max_iter': 1000}
    solver = casadi.nlpsol('solver', 'ipopt', input, ipopt_opt)
    output = solver(
        x0=np.concatenate((
            np.reshape(W_A_init_real, (elemNum*ueNum), order='F'), 
            np.reshape(W_A_init_imag, (elemNum*ueNum), order='F'))),
        lbg=W_A_power_min, ubg=W_A_power_max)

    W_A_col = casadi.reshape(output['x'], 2*elemNum*ueNum, 1)
    W_A_real_col = W_A_col[elemNum*ueNum:]
    W_A_imag_col = W_A_col[:elemNum*ueNum]
    W_A_real = casadi.reshape(W_A_real_col, elemNum, ueNum)
    W_A_imag = casadi.reshape(W_A_imag_col, elemNum, ueNum)
    W_A = np.array(W_A_real) + 1j * np.array(W_A_imag)
    W_A = np.multiply(W_A, W_A_mask_temp)
    return W_A



if __name__ == "__main__":
    ueNum = 2
    elemNum = 4
    W_A = np.exp(1j*np.random.uniform(0, 2*np.pi, (elemNum, ueNum))) # np.array([[1, 0], [-1, 0], [0, 1], [0, -1]])
    W_D = np.exp(1j*np.random.uniform(0, 2*np.pi, (ueNum, ueNum))) # np.array([[1, 0], [0, -1]])
    W_ZF = np.matmul(W_A, W_D)

    W_D_est = SolvePC_D(W_ZF, W_A)
    print(W_D)
    print(W_D_est)

    W_A_est = SolvePC_A(W_ZF, W_D)
    print(W_A)
    print(W_A_est)