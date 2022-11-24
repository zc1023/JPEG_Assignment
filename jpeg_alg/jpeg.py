import cv2
import numpy as np
from bitstream import BitStream
from config import *
from encode import *

class JPEG:
    def __init__(self,input_image,output_file,g_scale) -> None:
        self.image = input_image
        self.file = output_file
        self.lu_quant = lu_quant
        self.ch_quant = ch_quant

        self.lu_quant = np.array(np.floor((self.lu_quant * g_scale) / 8))
        self.lu_quant = np.where(self.lu_quant == 0, 1, self.lu_quant)
        self.lu_quant = np.where(self.lu_quant > 255, 255, self.lu_quant)
        self.lu_quant = self.lu_quant.reshape([8, 8]).astype(int)

        self.ch_quant = np.array(np.floor((self.ch_quant * g_scale ) / 8))
        self.ch_quant = np.where(self.ch_quant == 0, 1, self.ch_quant)
        self.ch_quant = np.where(self.ch_quant > 255, 255, self.ch_quant)
        self.ch_quant = self.ch_quant.reshape([8, 8]).astype(int)

        self.outputstream = BitStream()


    def __convert(self):
        '''
        args:
            image path
        returns:
            y,u,v
            
        '''

        image = cv2.imread(self.image)

        # print(image)
        image = cv2.copyMakeBorder(image, (8-image.shape[0]%8)%8, 0, (8-image.shape[1]%8)%8,0, cv2.BORDER_CONSTANT, value=(128,128,128)) #padding
        self.h, self.w = image.shape[:2]
        # print(self.h,self.w)
        b, g, r = cv2.split(image)

        y = 0.299*r + 0.5870*g + 0.114*b -127
        u = -0.1687*r - 0.3313*g + 0.5*b 
        v = 0.5*r - 0.4187*g - 0.0813*b 

        self.y_channel = y.astype(np.int32) 
        self.u_channel = u.astype(np.int32) 
        self.v_channel = v.astype(np.int32) 

    def __dct(self,image_block):
        '''
        args:
            8X8 image_block
        returns:
            8X8 dct_block
        '''
        dct_matrix = np.zeros((8,8))
        for i in range(8):
            for j in range(8):
                if i==0:
                    c = np.sqrt(1/8)
                else:
                    c = np.sqrt(2/8)
                dct_matrix[i][j] = c*np.cos(np.pi*(j+0.5)*i/8)
        dct_matrix_T = dct_matrix.transpose()
        return np.matmul(np.matmul(dct_matrix,image_block),dct_matrix_T)

    def __quantificate(self,dct_block,lu = 1):
        '''
        args:
            8x8 dct_block
        return:
            8x8 quantificated_block (int)
        '''
        
        # Q = np.array(Q)
        # Q.shape = [8,8] #the quantificate matrix 
        # print(self.Q)
        if lu==1:
            return np.rint(dct_block/(self.lu_quant)).astype(int)
        else:
            return np.rint(dct_block/self.ch_quant).astype(int)



    def __write(self):
        '''
        add jpeg head
        '''
        with open(self.file,'wb')as output:
            output.write(bytes.fromhex('FFD8FFE000104A46494600010100000100010000'))
            
            output.write(bytes.fromhex('FFDB004300'))
            self.lu_quant = self.lu_quant.reshape([64])
            output.write(bytes(self.lu_quant.tolist()))
            
    

            output.write(bytes.fromhex('FFDB004301'))
            self.ch_quant = self.ch_quant.reshape([64])
            output.write(bytes(self.ch_quant.tolist()))
            
            output.write(bytes.fromhex('FFC0001108'))
            output.write(bytes.fromhex((hex(self.h)[2:].rjust(4,'0'))))
            output.write(bytes.fromhex((hex(self.w)[2:].rjust(4,'0'))))
            output.write(bytes.fromhex('03011100021101031101'))
            output.write(bytes.fromhex(
            'FFC401A20000000701010101010000000000000000040503020601000708090A0B0100020203010101010100000000000000010002'
            '030405060708090A0B1000020103030204020607030402060273010203110400052112314151061361227181143291A10715B14223'
            'C152D1E1331662F0247282F12543345392A2B26373C235442793A3B33617546474C3D2E2082683090A181984944546A4B456D35528'
            '1AF2E3F3C4D4E4F465758595A5B5C5D5E5F566768696A6B6C6D6E6F637475767778797A7B7C7D7E7F738485868788898A8B8C8D8E8'
            'F82939495969798999A9B9C9D9E9F92A3A4A5A6A7A8A9AAABACADAEAFA110002020102030505040506040803036D01000211030421'
            '12314105511361220671819132A1B1F014C1D1E1234215526272F1332434438216925325A263B2C20773D235E2448317549308090A'
            '18192636451A2764745537F2A3B3C32829D3E3F38494A4B4C4D4E4F465758595A5B5C5D5E5F5465666768696A6B6C6D6E6F6475767'
            '778797A7B7C7D7E7F738485868788898A8B8C8D8E8F839495969798999A9B9C9D9E9F92A3A4A5A6A7A8A9AAABACADAEAFA'
            ))
            output_len = self.outputstream.__len__()

            pad = 8 - output_len%8
            if pad != 0:
                self.outputstream.write(np.ones([pad]).tolist(),bool)
            output.write(
                bytes([255, 218, 0, 12, 3, 1, 0, 2, 17, 3, 17, 0, 63, 0])
            )
            output_bytes = self.outputstream.read(bytes)
            
            
            for i in range(len(output_bytes)):
                output.write(bytes([output_bytes[i]]))
                if output_bytes[i] == 255:
                    output.write(bytes([0]))
            output.write(bytes([255,217]))

    def conpress(self):
        self.__convert()
        channels = (self.y_channel,self.u_channel,self.v_channel)
        # print(len(self.y_channel))

        pre_dc_component = [0,0,0]
        for y in range(0, self.h, 8):
            for x in range(0, self.w, 8):
                
                for j,channel in enumerate(channels):
                    #dct + quant + zig
                    # print(channel[i].shape)

                    _dct = self.__dct(channel[y:y+8,x:x+8])
                    # print(_dct)
                    _quant = self.__quantificate(_dct,j+1)
                    
                    # if  i==100 or i == 101:
                    #     print(_quant)
                    #dc encode
                    
                    dc_component = _quant[0][0]
                    # print(dc_encode(dc_component,pre_component=pre_dc_component[j]))

                    self.outputstream.write(dc_encode(dc_component,pre_component=pre_dc_component[j],lu=j+1),bool)

                    pre_dc_component[j]=dc_component

                    #ac encode

                    self.outputstream.write(ac_encode(_quant,lu=j+1),bool)


        #add jpeg head
        self.__write()

if __name__ == "__main__":
    jpg = JPEG('./data/input.png',"./figure/output8.jpg",64)
    jpg.conpress()