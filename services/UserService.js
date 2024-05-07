const { loginByAmkorAPI } = require('../utils/login.js')
const {
    signup,
    isExit
} = require('../models/users.js')
const { sign } = require('../utils/token.js')

class UserService {
    constructor() {}

    signIn = async(account, password) =>{
        const { isError, isValid } = await loginByAmkorAPI(account, password)
        if(isError){
            return {
                result: false,
                msg: isError
            }
        }else{
            if (isValid) {
                const isAlreadyExit = await isExit(account)
                if (!isAlreadyExit) {
                    let isSuccess = await signup({account, password})
                }
                const token = sign(account)
                return {
                    result: true,
                    token: token,
                    msg: 'Success!'
                }
            }else{
                return {
                    result: false,
                    msg: '帳號密碼錯誤'
                }
            }
        }
    }
}

module.exports = UserService