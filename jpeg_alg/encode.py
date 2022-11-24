from config import *
import numpy as np



def dc_encode(dc_component: int,pre_component = 128, lu = 1) -> str: 
    '''
    args:
        the list of dc component 
    returns:
        a string of dc code
    '''
    dc_code_string = []

    amplitude = dc_component - pre_component

    if amplitude == 0:
        size = 0
    else:
        size = int(np.log2(np.abs(amplitude)))+1
    if lu == 1:
        size_code = DCLuminanceSizeToCode[size]
    else:
        size_code = DCChrominanceSizeToCode[size]
    dc_code_string += size_code

    amplirude_code = bin(np.abs(amplitude))[2:]
    if amplitude != 0:
        if amplitude > 0:
            dc_code_string += amplirude_code
        else:
            for i in amplirude_code:
                if i == '0':
                    dc_code_string += '1'
                if i == '1':
                    dc_code_string += '0'

    # pre_component = component
    return [int(i) for i in dc_code_string]

def z_scan(ac_matrix)->list:
    '''
    args:
        8x8-1 ac component_matrix
    return:
        63 array
        the last non-zero position 
    '''
    res = []
  
    for i in range(len(pot_x)):
        res.append(ac_matrix[pot_x[i]][pot_y[i]])
       
    return res
    
def ac_encode_exec(runlength:int,amplitude:int,lu=1)->str:
    '''
    execute every time non-zero value is encountered or runlength reaches 16
    agrs:
        runlength: count of consecutive zeros
        size: log size of amplitude
        amplitude: the non-zero value
    returns:
        code:str
    '''

    res =''
    if amplitude == 0:
        size = 0
    else:
        size = int(np.log2(np.abs(amplitude)))+1
    run_size = str.upper(str(hex(runlength))[2:]) + str.upper(str(hex(size))[2:])
    
    if lu == 1:
        code =  ACLuminanceSizeToCode[run_size]
    else :
        code = ACChrominanceToCode[run_size]
    res+=''.join(map(lambda x:str(x), code))

    if amplitude != 0: 
        amplirude_code = bin(np.abs(amplitude))[2:]
        if amplitude >= 0:
            res += amplirude_code
        else:
            for i in amplirude_code:
                if i == '0':
                    res += '1'
                if i == '1':
                    res += '0'
    return res

def ac_encode(dct_matrix,lu=1)->str:
    '''
    encode the AC component 
    args:
        dct_matrix:8X8
    returns:
        encoded string
    '''
    ac_component = z_scan(dct_matrix)
    zeronum = 0
    res = ''
    
    for ac in ac_component:
        
        if ac != 0:
            # print(ac)
            if zeronum > 15:
                for _ in range(zeronum//15):
                    res += ac_encode_exec(15,0,lu=lu)
            res += ac_encode_exec(zeronum%15,ac,lu=lu)
            zeronum = 0
        elif ac == 0:
            zeronum += 1

    if ac == 0:
        res += ac_encode_exec(0,0,lu=lu)
    # print(res)
    return [int(i) for i in res]

if __name__ =='__main__':
    test_m = np.array(
        [[-6,-3,3,0,0,0,0,0],
[0,0,0,0,0,0,0,0],
[0,0,0,0,0,0,0,0],
[0,0,0,0,0,0,0,0],
[0,0,0,0,0,0,0,0],
[0,0,0,0,0,0,0,0],
[0,0,0,0,0,0,0,0],
[0,0,0,0,0,0,0,1]]
 )
    test_m.shape=(8,8)
    print(len(ac_encode(test_m,lu=2)))
    print((ac_encode(test_m,lu=2)))
    # for i in range(10):
    #     print(dc_encode(-117,pre_component=-117,lu=2+1))