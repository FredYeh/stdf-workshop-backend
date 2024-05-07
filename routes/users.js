var express = require('express')
var router = express.Router()
const {
    userRegister,
    userLogin,
    userList,
    modifyUserInfo,
    deleteUser,
    userSignout,
    getUserInfo,
    setEmail,
} = require('../controllers/user.js')
const { auth } = require('../middlewares/auth')

router.post('/register', userRegister)

router.post('/setEmail', auth, setEmail)

router.post('/login', userLogin)

router.get('/list', userList)

router.post('/modify', auth, modifyUserInfo)

router.post('/delete', auth, deleteUser)

router.post('/signout', userSignout)

router.get('/getUserInfo', auth, getUserInfo)

module.exports = router
