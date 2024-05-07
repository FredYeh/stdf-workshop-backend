const { Users } = require('../utils/dbTool/schema/user')
const { encode } = require('../utils/encryptTool/encrypt.js')

/**
 * To signup the user Infomation
 * return has been saved in DB or not
 * @param  { username, password, email }
 * @returns { Boolean }
 */
const signup = async ({ account, password }) => {
    const encodePassword = await encode(password)
    // 创建一个实例调用save方法，讲数据存入到数据库中
    const users = new Users({
        account,
        password: encodePassword,
    })
    users
        .save()
        .then(() => {
            return true
        })
        .catch((err) => {
            console.log('err' + err)
            return false
        })
}

/**
 *  To check the username or email has been used or not
 * @param String
 * @returns { Boolean }
 */
const isExit = async (account) => await Users.exists({ account: account })


const getAccount = async (account) => await Users.findOne({ account: account }).exec()

const updateEmailByAccount = async (account, email) =>
    await Users.updateOne({ account: account }, { $set: { email: email } })

const findList = async (n = 0) =>
    Users.find({}, { _id: 1, password: 0, __v: 0, isAdmin: 0 })
        .sort({ _id: -1 })
        .skip(n)

/**
 * to modify the user information by user id
 * @param {*} id
 * @param {*} options
 */
const modifyUserInfoById = async (id, options) =>
    new Promise((resolve, _) => {
        Users.findByIdAndUpdate(id, { $set: options }, (err, doc) => {
            if (!err) resolve(true)
            else {
                console.log(doc)
                resolve(false)
            }
        })
    })

const deleteUserById = (_id) =>
    new Promise((resolve, _) => {
        console.log(_id)
        Users.findByIdAndRemove(_id, (err, doc) => {
            if (!err) resolve(true)
            else {
                console.log(doc)
                resolve(false)
            }
        })
    })

const checkUserAuth = async (account) => {
    return new Promise(async (resolve, reject) => {
        Users.findOne({ account: account }, (err, doc) => {
            const isExit = !!doc
            const isAdmin = isExit ? doc.isAdmin : false
            resolve({
                isExit,
                isAdmin,
            })
        })
    })
}

module.exports = {
    signup,
    isExit,
    getAccount,
    findList,
    modifyUserInfoById,
    deleteUserById,
    checkUserAuth,
    updateEmailByAccount,
}
