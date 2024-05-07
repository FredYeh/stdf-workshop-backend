const mongoose = require('mongoose')
const dayjs = require('dayjs')
const userSchema = mongoose.Schema(
    {
        account: String,
        password: String,
        email: { type: String, default: '' },
        // createdTime: { type: Date, default: Date.now },
        lastestLogin: {
            type: String,
            default: dayjs(Date.now()).locale('zh-tw').format('YYYYMMDD'),
        },
        isAdmin: { type: Boolean, default: false },
        roles: { type: Array, default: ['editor'] },
        avatar: {
            type: String,
            default:
                'https://wpimg.wallstcn.com/007ef517-bafd-4066-aae4-6883632d9646',
        },
        // perspective: { type: String, default: 'customer' },
    },
    { versionKey: false }
)
userSchema.set('collection', 'users')
exports.Users = mongoose.model('users', userSchema)
